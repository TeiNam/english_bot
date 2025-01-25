// config/api.ts

import {ensureHttps} from "../utils/url.ts";

interface ApiConfig {
 baseURL: string;
 headers: {
   'Content-Type': string;
   'Accept': string;
   'Access-Control-Allow-Origin': string;
   'Access-Control-Allow-Methods': string;
   'Access-Control-Allow-Headers': string;
 };
}

const API_CONFIG: ApiConfig = {
 baseURL: ensureHttps(import.meta.env.VITE_API_URL),
 headers: {
   'Content-Type': 'application/json',
   'Accept': 'application/json',
   'Access-Control-Allow-Origin': '*',
   'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, PATCH, OPTIONS',
   'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept',
 },
};

export { API_CONFIG };