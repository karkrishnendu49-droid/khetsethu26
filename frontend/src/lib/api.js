import axios from 'axios';

export const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
export const api = axios.create({ baseURL: API, withCredentials: true });
export const fmt = (n) => new Intl.NumberFormat('en-IN').format(n || 0);
export const cropEmoji = (c) => c === 'Tomato' ? '🍅' : c === 'Potato' ? '🥔' : c === 'Onion' ? '🧅' : '🌾';
