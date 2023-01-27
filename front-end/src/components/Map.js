import React, { useRef, useState, useEffect } from 'react';
import mapboxgl, { clearStorage } from 'mapbox-gl';
import './Map.css'

export default function Map({wsjState, nytState}) {

  const [WsJArticles, setWsJArticles] = useState([])
  const [NytArticles, setNytArticles] = useState([])

  useEffect(() => {
    fetch('http://api.opticmap.uk/wsjlist/')
        .then(r => r.json())
        .then(d => setWsJArticles(d))
        .catch(e => console.log(e))
  }, [])

  useEffect(() => {
    fetch('http://api.opticmap.uk/nytlist/')
        .then(r => r.json())
        .then(d => setNytArticles(d))
        .catch(e => console.log(e))
  }, [])

  mapboxgl.accessToken = 'pk.eyJ1IjoiZ2F1cmF2LW5hcmF5YW4tdmFybWEiLCJhIjoiY2w4YzM5Z28xMDJ0czN4bW92YmJoZjJ0NSJ9.lL6EtiXJOEY-f_4hmKDn5w'
  
  const mapContainer = useRef(null);
  const map = useRef(null);
  const [lng, setLng] = useState(-25.0);
  const [lat, setLat] = useState(32.35);
  const [zoom, setZoom] = useState(1.2);
  
  useEffect(() => {
    // initialize map only once
    if (map.current) return;

    // make sure articles are populated before heading into 2nd useEffect
    if (WsJArticles.length == 0) return
    if (NytArticles.length == 0) return

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/light-v10',
      center: [lng, lat],
      zoom: zoom
    });
  });
  
  // loading in the map source and layers + updating it 
  useEffect(() => {
    if (!map.current) return

    // making a map of country frequency (i.e. {US:2,RU:3})
    const countryFrequencyMap = {}
    function processArticles(articles) {
      for (let article of articles) {
        const array = eval(article.entity);
        for (let country of array) {
          (country in countryFrequencyMap) ? countryFrequencyMap[country]++ : countryFrequencyMap[country] = 1
        }
      }
    }

    let dummy = true
    wsjState ? processArticles(WsJArticles) : dummy = false;
    nytState ? processArticles(NytArticles) : dummy = false;

    // the countryfrequencymap is used to make the filters...
    const mainFilterArray = []
    const colorFilterArray = []
    const opacityFilterArray = []
    const lineColorFilterArray = []
    const lineWidthFilterArray = []

    // ...iterate through country frequency map to accomplish this
    Object.keys(countryFrequencyMap).forEach((country) => {
      mainFilterArray.push(['==', ['get', 'iso_3166_1'], `${country}`])

      opacityFilterArray.push(['==', ['get', 'iso_3166_1'], `${country}`])
      opacityFilterArray.push(.5)

      lineColorFilterArray.push(['==', ['get', 'iso_3166_1'], `${country}`])
      lineColorFilterArray.push('#0107ff')

      lineWidthFilterArray.push(['==', ['get', 'iso_3166_1'], `${country}`])
      lineWidthFilterArray.push(.25)

      if (countryFrequencyMap[country] == 1) {
        colorFilterArray.push(['==', ['get', 'iso_3166_1'], `${country}`])
        colorFilterArray.push('#cdcdf1')

      } if (countryFrequencyMap[country] == 2) {
        colorFilterArray.push(['==', ['get', 'iso_3166_1'], `${country}`])
        colorFilterArray.push('#a6a4fb')

      } if (countryFrequencyMap[country] == 3) {
        colorFilterArray.push(['==', ['get', 'iso_3166_1'], `${country}`])
        colorFilterArray.push('#807bff')

      } if (countryFrequencyMap[country] == 4) {
        colorFilterArray.push(['==', ['get', 'iso_3166_1'], `${country}`])
        colorFilterArray.push('#554eff')

      } if (countryFrequencyMap[country] >= 5) {
        colorFilterArray.push(['==', ['get', 'iso_3166_1'], `${country}`])
        colorFilterArray.push('#0107ff')
      }
    })

    colorFilterArray.push('purple')
    opacityFilterArray.push(1)
    lineColorFilterArray.push('black')
    lineWidthFilterArray.push(0)

    const mainFilter = {'filter': ['any', ...mainFilterArray]}
    const colorFilter = {'fill-color': ['case', ...colorFilterArray]}
    const opacityFilter = {'fill-opacity': ['case', ...opacityFilterArray]}
    const lineColorFilter = {'line-color': ['case', ...lineColorFilterArray]}
    const lineWidthFilter = {'line-width': ['case', ...lineWidthFilterArray]}

    map.current.on('idle', () => {
      // updating the main filter
      map.current.setFilter('state', mainFilter['filter'])

      // updating the paint properties
      map.current.setPaintProperty('state', 'fill-color', colorFilter['fill-color'])
      map.current.setPaintProperty('state', 'fill-opacity', opacityFilter['fill-opacity'])

      // updating border properties
      map.current.setPaintProperty('state-border', 'line-color', lineColorFilter['line-color'])
      map.current.setPaintProperty('state-border', 'line-width', lineWidthFilter['line-width'])
    })

    map.current.on('load', () => {
      map.current.addSource('countries', {
        'type': 'vector',
        'url': 'mapbox://mapbox.country-boundaries-v1'
      });
      map.current.addLayer({
        'id': 'state',
        'type': 'fill',
        'source-layer': 'country_boundaries',
        'source': 'countries',
        'paint': {
          ...colorFilter,
          ...opacityFilter,
        },
        ...mainFilter,
        'layout': {
          // Make the layer visible by default.
          'visibility': 'visible'
          }
      });
      map.current.addLayer({
        'id': 'state-border',
        'type': 'line',
        'source': 'countries',
        'source-layer': 'country_boundaries',
        'paint': {
            ...lineColorFilter,
            ...lineWidthFilter,
            'line-dasharray': [10, 5],
        },
        'layout': {
          // Make the layer visible by default.
          'visibility': 'visible'
          }
      });
    });

    const onStateClick = (e) => {
      const popupList = document.getElementsByClassName('mapboxgl-popup');
      console.log(popupList.length)
      while (popupList.length > 0) {
        popupList[0].remove();
      }

      const coordinates = e.lngLat;
      const countryEng = e.features[0].properties.name_en;
      
      const countryISO = e.features[0].properties.iso_3166_1;
      
      const popup = new mapboxgl.Popup({ 
        closeOnClick: true,
        anchor: 'top',
      });
      
      // aggregate list of articles about clicked country
      let allArticles = []
      let dummy = true
      wsjState ? allArticles = allArticles.concat(WsJArticles) : dummy = false
      nytState ? allArticles = allArticles.concat(NytArticles) : dummy = false
  
      const countryArticles = allArticles.filter(article => article.entity.includes(countryISO));
  
      // construct list out of all articles
      const articlesList = countryArticles.map(article => `<li>${article.title}</li>`).join('');

      popup.setLngLat(coordinates).setHTML(`
        <div>
          <h4>${countryEng}</h4>
          <ul>
            ${articlesList}
          </ul>
        </div>
      `)
      .addTo(map.current);
    }

    map.current.on('click', 'state', onStateClick);

    map.current.on('mousemove', 'state', (e) => {
      // Change the cursor style as a UI indicator.
      map.current.getCanvas().style.cursor = 'pointer';
    });

    map.current.on('mouseleave', 'state', () => {
      map.current.getCanvas().style.cursor = '';
    });
  }, [WsJArticles, NytArticles, wsjState, nytState]) 
  
  return (
    <div ref={mapContainer} className="map-container" />
  )
}