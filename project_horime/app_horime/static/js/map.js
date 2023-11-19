
const shelter_flood = [
  { label: "1", name: "예천군청", lat: 36.657983, lng: 128.452769 },
  { label: "2", name: "삼우목련아파트", lat: 36.651225, lng: 128.442261 },
  { label: "3", name: "예천군의회", lat: 36.656875, lng: 128.452828 },
  { label: "4", name: "예천우체국", lat: 36.657097, lng: 128.452431 },
  { label: "5", name: "예천교육청", lat: 36.655603, lng: 128.454547 },
  { label: "6", name: "세종타운", lat: 36.654711, lng: 128.448914 },
  { label: "7", name: "세아아파트 102동", lat: 36.645672, lng: 128.463594 },
  { label: "8", name: "예천대심 국민임대아파트 103동", lat: 36.65255, lng: 128.441739 },
  { label: "9", name: "예천대심 국민임대아파트 지하주차장", lat: 36.652586, lng: 128.441744 },
  { label: "10", name: "조일리버빌 지하주차장", lat: 36.655856, lng: 128.458306 },
  { label: "11", name: "두영서부빌라", lat: 36.654356, lng: 128.447972 },
  { label: "12", name: "무궁화아파트", lat: 36.657603, lng:128.454289 },
  { label: "13", name: "덕흥장미아파트 101동", lat: 36.649139, lng: 128.441119 },
  { label: "14", name: "덕흥장미아파트 103동", lat: 36.649111, lng: 128.441089 },
  { label: "15", name: "세아아파트 101동", lat: 36.645786, lng:128.464242 },
];

const shelter_avalanche = [
  { label: "1", name: "본리 경로당", lat: 36.599009, lng: 128.49251 },
  { label: "2", name: "본리 밭마경로당", lat: 36.599849, lng: 128.49016 },
  { label: "3", name: "원곡리마을회관", lat: 36.595368, lng: 128.43894 },
  { label: "4", name: "기곡1리경로당", lat: 36.706403, lng: 128.57121 },
  { label: "5", name: "수계2리마을회관", lat: 36.672216, lng: 128.54435 },
  { label: "6", name: "우래1리마을회관", lat: 36.692766, lng: 128.57115 },
];

let markers_flood = [];
let markers_avalanche = [];
  
window.initMap = function () {
  const map = new google.maps.Map(
    document.getElementById("map"), {
      center: { lat: 36.66154100010838, lng: 128.5135448823666 },
      zoom: 17,
      mapId: '5f1293dcfc619b31'
    }
  );
  const bounds = new google.maps.LatLngBounds();
  const infoWindow = new google.maps.InfoWindow();

  shelter_flood.forEach(({ label, name, lat, lng }) => {
    const marker = new google.maps.Marker({
      position: { lat, lng },
      //label,
      map,
      visible: false,
    });
    // bounds.extend(marker.position);
    marker.addListener("click", () => {
      map.panTo(marker.position);
      infoWindow.setContent(name);
      infoWindow.open({
        anchor: marker,
        map
      });
    });
    markers_flood.push(marker);
  });

  shelter_avalanche.forEach(({ label, name, lat, lng }) => {
    const marker = new google.maps.Marker({
      position: { lat, lng },
      //label,
      map,
      visible: false,
    });
    // bounds.extend(marker.position);
    marker.addListener("click", () => {
      map.panTo(marker.position);
      infoWindow.setContent(name);
      infoWindow.open({
        anchor: marker,
        map
      });
    });
    markers_avalanche.push(marker);
  });
  // map.fitBounds(bounds);
};

function toggleFlood() {
    markers_flood.forEach(marker => {
        marker.setVisible(!marker.getVisible());
    });
} 

function toggleAval() {
    markers_avalanche.forEach(marker => {
        marker.setVisible(!marker.getVisible());
    });
} 