
const client_id = 'NEh3V0ZjaE1fT1Nkdk9jMnJlSGNQQTo1NzRiNDEwZmM3MzZhNmIw';

let mly;
let map;
let flying = false;
let gpx_line;
let camera_marker;
let camera_node;
let gpx_points;

init();

function init(){
	initPhoto();
	initMap();
	const fileSelector = document.getElementById('file-selector');
	fileSelector.addEventListener('change', (event) => {
	  const fileList = event.target.files;
	  console.log(fileList);
	  openGpx(fileList[0]);
	});

}

function openGpx(file){
	const reader = new FileReader();
	reader.addEventListener('load', (event) => {
		const content = event.target.result;
		const parser = new DOMParser();
		const xml = parser.parseFromString(content, "text/xml");
		console.log(xml);
		gpx_points = convertXmlToPoints(xml);
		//console.log(xml, JSON.stringify(points));
		const latlngs = getlatlngs(gpx_points);
		
		let layers = [];
		
		for (let i = 0; i < latlngs.length -1; i++){

			const a = i/latlngs.length;
			const rgb = hsvToRgb16(360*a, 100, 100);
			const color = rgb2hex([rgb.red, rgb.green, rgb.blue]);
			const layer = L.polyline([latlngs[i],latlngs[i+1]], {color: color});
			layers.push(layer);
		}
		if(gpx_line) gpx_line.remove();
		gpx_line = L.featureGroup(layers).addTo(map);
		//---
		/*
		function getColor(x) {
			return x < 10     ?    '#000000':
				   x < 100     ?   '#0000ff':
				   x < 200     ?   '#00ff00':
				   x < 300     ?   '#ff0000':
									'#ffffff' ;
		  };

		const geojson = toGeoJSON.gpx(xml);
		gpx_line = L.geoJson(geojson, {
			style: function (feature) {
				console.log(feature);
				return {
				 "color": getColor(feature.geometry.coordinates[2]),
				 "opacity": 1,
				}}
		}).addTo(map);
		*/
		//console.log(JSON.stringify(geojson, null, 2));
		//---

		//gpx_line = L.polyline(latlngs, {color: 'red'}).addTo(map);
		const position = 0;
		moveCloseTo360(gpx_points[position].lat, gpx_points[position].lon)
	
		map.fitBounds(L.latLngBounds(latlngs));
		
	  });
	reader.readAsText(file);
}

function moveCloseTo360(lat, lon){

	const url = `https://a.mapillary.com/v3/images?client_id=${client_id}&pano=true&per_page=1&radius=1000&closeto=${lon},${lat}`;
	let request = new XMLHttpRequest();
	request.open('GET', url , true);
	request.onload = function () {
	
		data = this.response;
		const json = JSON.parse(data);
		if (json.features.length < 1) {
			alert("No 360 photo around here");
			return;
		}
		const coordinates = json.features[0].geometry.coordinates;
		const position = 1000;
		mly.moveCloseTo(coordinates[1], coordinates[0]).then(
			(n) => {
				console.log(n);
				//showGpxOnPhoto(gpx_points, gpx_points[position].ele);
			},
			(e) => { console.error(e); });
	}
	request.send();
}

function rgb2hex ( rgb ) {
	return "#" + rgb.map( function ( value ) {
		return ( "0" + value.toString( 16 ) ).slice( -2 ) ;
	} ).join( "" ) ;
}
//http://shanabrian.com/web/javascript/color-code-convert-hsv-to-16rgb.php
var hsvToRgb16 = function(hue, saturation, value) {
	    var result = false;
	 
	    if (((hue || hue === 0) && hue <= 360) && ((saturation || saturation === 0) && saturation <= 100) && ((value || value === 0) && value <= 100)) {
	        var red   = 0,
	            green = 0,
	            blue  = 0,
	            i     = 0,
	            f     = 0,
	            q     = 0,
	            p     = 0,
	            t     = 0;
	 
	        hue        = Number(hue)        / 60;
	        saturation = Number(saturation) / 100;
	        value      = Number(value)      / 100;
	 
	        if (saturation === 0) {
	            red   = value;
	            green = value;
	            blue  = value;
	        } else {
	            i = Math.floor(hue);
	            f = hue - i;
	            p = value * (1 - saturation);
	            q = value * (1 - saturation * f);
	            t = value * (1 - saturation * (1 - f));
	 
	            switch (i) {
	                case 0 :
	                    red   = value;
	                    green = t;
	                    blue  = p;
	                    break;
	                case 1 :
	                    red   = q;
	                    green = value;
	                    blue  = p;
	                    break;
	                case 2 :
	                    red   = p;
	                    green = value;
	                    blue  = t;
	                    break;
	                case 3 :
	                    red   = p;
	                    green = q;
	                    blue  = value;
	                    break;
	                case 4 :
	                    red   = t;
	                    green = p;
	                    blue  = value;
	                    break;
	                case 5 :
	                    red   = value;
	                    green = p;
	                    blue  = q;
	                    break;
	            }
	        }
	 
	        result = {
	            red   : Math.round(red   * 255).toString(16),
	            green : Math.round(green * 255).toString(16),
	            blue  : Math.round(blue  * 255).toString(16)
	        };
	    }
	 
	    return result;
	};


function eleFromGpx(lat,lon){
	let nearest_distance = 100000;
	let nearest_ele;
	for (let i = 0; i < gpx_points.length; i++){
		const dlat = lat - gpx_points[i].lat;
		const dlon = lon - gpx_points[i].lon;
		const distance = Math.pow(dlat**2 + dlon**2, 0.5);
		if (distance < nearest_distance){
			nearest_distance = distance ;
			nearest_ele = gpx_points[i].ele;
		}
		
	}
	return nearest_ele;
}

function showGpxOnPhoto(points, base_ele){




	const tagComponent = mly.getComponent("tag");
	tagComponent.removeAll();

	let pointTags = [];
	for (let i = 0; i < points.length; i++){
		const point = points[i];
		const xy = getXY(camera_node.latLon, point, 2 + Number(base_ele) - Number(point.ele), camera_node.ca);
		const pointGeometry = new Mapillary.TagComponent.PointGeometry([xy.x, xy.y]);
		const a = i/points.length;
		//const color = rgb2hex([0 + a, 0 + a, 255]);
		const rgb = hsvToRgb16(360*a, 100, 100);
		const color = rgb2hex([rgb.red, rgb.green, rgb.blue]);
		const pointTag = new Mapillary.TagComponent.SpotTag('pointTag' + i, pointGeometry, {color: color});
		pointTags.push(pointTag);
	}

	tagComponent.add(pointTags);

	/*
	const markerComponent = mly.getComponent('marker');
	let markers = [];
	for (let i = 0; i < points.length; i++){
		const point = points[i];

		const marker = new Mapillary.MarkerComponent.CircleMarker(i.toString(), point, { radius: 0.5, color: '#0ff' });
		markers.push(marker);
	}
	markerComponent.add(markers);
	*/
}

function convertXmlToPoints(xml){
	let points = [];
	const trk = xml.getElementsByTagName('trk'); // 入れ子構造になっている
    for (i=0; i < trk.length; i++) {
        const trkseg = trk[i].getElementsByTagName('trkseg');
        for (j=0; j < trkseg.length; j++) {
            let trkpt = trkseg[j].getElementsByTagName('trkpt');
            for (k=0; k < trkpt.length; k++) {
				let point = {};
				// ... の lat と lon を取り出す。
				point.lat = trkpt[k].attributes.getNamedItem("lat").nodeValue;
				point.lon = trkpt[k].attributes.getNamedItem("lon").nodeValue;
				point.ele = trkpt[k].getElementsByTagName('ele')[0].childNodes[0].nodeValue;
				point.time = trkpt[k].getElementsByTagName('time')[0].childNodes[0].nodeValue;
				points.push(point);
            }
        }
	}
	return points;
}

function getlatlngs(points){
	let latlngs = [];
	for (let i=0; i < points.length; i++){
		latlngs.push([points[i].lat, points[i].lon]);
	}
	return latlngs;
}

function getXYs(target){
	const position = mly.getPosition();

}

function getXY(base, target, height, bearing){
	
	const dlat = target.lat - base.lat;
	const dlon = target.lon - base.lon;
	

	
	const dy = R * Math.sin(dlat /180 * Math.PI);
	const dx = R * Math.cos(base.lat / 180 * Math.PI) * Math.sin(dlon / 180 * Math.PI);
	
	let target_bearing = Math.atan(dx/dy) * 180 / Math.PI;
	if (dy < 0) {target_bearing += 180;}
	
	const relative_bearing = target_bearing - bearing;
	
	const distance = Math.pow(dx**2+dy**2,0.5);
	
	const target_angle = Math.atan(height/distance) * 180 / Math.PI;
	
	const theta = target_angle;
	const phi = relative_bearing;
	
	const x = (((phi + 180) + 360) % 360)/360;
	const y = 0.5 + theta/90*0.5;
	
	return {x:x, y:y, distance:distance, osm: target};

	
}

function initPhoto(){
	mly = new Mapillary.Viewer(
		'mly',
		client_id,
		// photo id
		null,
		{
			component: {
				cover: false,
				tag: true,
				marker: true,
			},
		});
		mly.setFilter(["==", "fullPano", true]);


		mly.on(Mapillary.Viewer.nodechanged, function(node) {
			camera_node = node;
			if(camera_marker) camera_marker.remove();
			const icon = L.icon({
				iconUrl: 'icon.png',
				iconRetinaUrl: 'icon.png',
				iconSize: [50, 50],
				iconAnchor: [25, 25],
				popupAnchor: [25, -25],
				className: "marker_icon",
			});
			camera_marker = L.marker([node.latLon.lat, node.latLon.lon], {icon: icon,rotationAngle: 0,}).addTo(map);
			//camera_marker.setLatLng([node.latLon.lat, node.latLon.lon]);

			console.log("nodechanged");

			map.panTo(node.latLon);
			const ele = eleFromGpx(node.latLon.lat, node.latLon.lon);
			document.getElementById("elevation").value = Math.round(ele);
			showGpxOnPhoto(gpx_points, ele);

		});
		mly.on(Mapillary.Viewer.povchanged, function(node) {

			mly.getPointOfView().then((pov) => {
				//camera_marker.addTo(map)
				camera_marker.setRotationAngle(pov.bearing);
			});

		});

}

function onElevationChange(){
	const ele = document.getElementById("elevation").value;
	showGpxOnPhoto(gpx_points, ele);
}

function initMap(){
	//地図を表示するdiv要素のidを設定
	map = L.map('mapcontainer');


  //表示するタイルレイヤのURLとAttributionコントロールの記述を設定して、地図に追加する
  const osmLayer = L.tileLayer('http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
	  attribution: "(C)<a href='https://www.openstreetmap.org/copyright' target='_blank'>OpenStreetMap contributors</a>",
	  maxZoom: 23,
	  maxNativeZoom: 19,
	  minZoom: 1,
	  //maxBounds: [[35.47, 139.62], [35.45, 139.64]],
  });
  map.setView([37.9243912, 139.045191], 5);	//日本全域

  /*
  const hash = new L.Hash(map);
  const url = location.href;
  const match = url.match(/#(\d{1,2})\/(-?\d[0-9.]*)\/(-?\d[0-9.]*)/);
  if (match){
      const [, zoom, lat, lon] = match;
      map.setView([lat, lon], zoom);
  } else {
      
  }
  */

  const kokudoLayer = L.tileLayer('https://cyberjapandata.gsi.go.jp/xyz/seamlessphoto/{z}/{x}/{y}.jpg',{
	attribution: '© <a href="https://maps.gsi.go.jp/development/ichiran.html">国土地理院</a>',
	maxZoom: 23,
	maxNativeZoom: 18,
    minZoom: 1,
    minNativeZoom: 2,
	}).addTo(map);
	
	const baseMap = {
        "国土地理院シームレス":kokudoLayer,
        "OpenStreetMap":osmLayer,

	};
 
	const mapillaryLayer = L.tileLayer('https://raster-tiles.mapillary.com/v0.1/{z}/{x}/{y}.png',{
		attribution: '(C)<a href="https://www.mapillary.com/">Mapillary</a>, CC BY',
	  maxZoom: 21,
	  maxNativeZoom: 17,
	});
	mapillaryLayer.setOpacity(0.65);
	const overlayLayer = {
		"Mapillary":mapillaryLayer,
	}
	//レイヤ設定
	const layerControl = L.control.layers(baseMap,overlayLayer,{"collapsed":true,});
    layerControl.addTo(map);

	map.options.singleClickTimeout = 250;
	map.on('click',function ( e ) {
		moveCloseTo360(e.latlng.lat, e.latlng.lng);
  
		  } );

}



const R = 6378100;	
function getDistancePhi(base, target){
	const x1 = rad(base.lng);
	const y1 = rad(base.lat);
	const x2 = rad(target.lng);
	const y2 = rad(target.lat);

	const dx = x2 - x1;

	const distance = R * Math.acos(Math.sin(y1)*Math.sin(y2) + Math.cos(y1)*Math.cos(y2)*Math.cos(dx));
	const phi = 90 - deg(Math.atan2( Math.cos(y1)*Math.tan(y2) - Math.sin(y1)*Math.cos(dx), Math.sin(dx)));

	return [distance, phi];
}
function rad(deg){
	return deg/180*Math.PI;
}

function deg(rad){
	return rad/Math.PI*180;
}