/**
 * Approximate geographic centroids (lat, lng) for the 54 AfCFTA member states,
 * keyed by ISO3 code. Used to place proportional-symbol markers on the Africa map.
 * Coordinates are standard country centroids (factual geographic constants).
 */
export const AFRICA_CENTROIDS = {
  DZA: [28.0, 1.7],   AGO: [-11.2, 17.9], BEN: [9.3, 2.3],    BWA: [-22.3, 24.7],
  BFA: [12.2, -1.6],  BDI: [-3.4, 29.9],  CMR: [7.4, 12.4],   CPV: [16.0, -24.0],
  CAF: [6.6, 20.9],   TCD: [15.5, 18.7],  COM: [-11.6, 43.3], COG: [-0.8, 15.2],
  COD: [-2.9, 23.6],  CIV: [7.5, -5.5],   DJI: [11.8, 42.6],  EGY: [26.8, 30.8],
  GNQ: [1.6, 10.3],   ERI: [15.2, 39.8],  SWZ: [-26.5, 31.5], ETH: [9.1, 40.5],
  GAB: [-0.6, 11.6],  GMB: [13.4, -15.4], GHA: [7.9, -1.0],   GIN: [9.9, -9.7],
  GNB: [12.0, -15.0], KEN: [0.0, 37.9],   LSO: [-29.6, 28.2], LBR: [6.4, -9.4],
  LBY: [26.3, 17.2],  MDG: [-18.8, 46.9], MWI: [-13.3, 34.3], MLI: [17.6, -4.0],
  MRT: [21.0, -10.9], MUS: [-20.3, 57.6], MAR: [31.8, -7.1],  MOZ: [-18.7, 35.5],
  NAM: [-22.6, 17.2], NER: [17.6, 8.1],   NGA: [9.1, 8.7],    RWA: [-1.9, 29.9],
  STP: [0.2, 6.6],    SEN: [14.5, -14.5], SYC: [-4.7, 55.5],  SLE: [8.5, -11.8],
  SOM: [5.2, 46.2],   ZAF: [-30.6, 22.9], SSD: [7.9, 30.0],   SDN: [15.5, 30.2],
  TZA: [-6.4, 34.9],  TGO: [8.6, 0.8],    TUN: [33.9, 9.6],   UGA: [1.4, 32.3],
  ZMB: [-13.1, 27.8], ZWE: [-19.0, 29.2],
};

export default AFRICA_CENTROIDS;
