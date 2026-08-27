import { createContext, useContext, useState } from 'react';

export const LANGS = [['en', 'English'], ['bn', 'বাংলা'], ['hi', 'हिंदी']];

const T = {
  en: {
    dashboard: 'Dashboard', my_produce: 'My produce', browse_produce: 'Browse produce', orders: 'Orders', my_orders: 'My orders',
    market_prices: 'Market prices', notifications: 'Notifications', settings: 'Settings', logout: 'Log out', admin_view: 'Admin view',
    add_produce: 'Add produce', edit: 'Edit', delete: 'Delete', place_order: 'Place order', accept: 'Accept', reject: 'Reject',
    track_order: 'Track order', search: 'Search', quantity: 'Quantity', price: 'Price', available: 'Available', low_stock: 'Low stock',
    sold_out: 'Sold out', earnings: 'Earnings', pending_orders: 'Pending orders', completed_orders: 'Completed orders',
    total_produce: 'Total produce', active_orders: 'Active orders', total_spent: 'Total spent', available_produce: 'Available produce',
    recent_orders: 'Recent orders', route: 'Route', home: 'Home', profile: 'Profile', farmer: 'Farmer', buyer: 'Buyer',
    order_placed: 'Order placed! The farmer has been notified.', mark_preparing: 'Start preparing', mark_out_for_delivery: 'Out for delivery',
    mark_delivered: 'Mark delivered', asking_price: 'asking price', market_price: 'Market price', view_all: 'View all',
    all_crops: 'All crops', all_locations: 'All locations', max_price: 'Max price', only_available: 'In stock only',
    list_view: 'List view', map_view: 'Map view', forgot_password: 'Forgot password?', reset_password: 'Reset password',
    new_password: 'New password', login: 'Log in', signup: 'Create account',
    status_placed: 'Placed', status_accepted: 'Accepted', status_rejected: 'Rejected', status_preparing: 'Preparing',
    status_out_for_delivery: 'Out for delivery', status_delivered: 'Delivered',
  },
  bn: {
    dashboard: 'ড্যাশবোর্ড', my_produce: 'আমার ফসল', browse_produce: 'ফসল দেখুন', orders: 'অর্ডার', my_orders: 'আমার অর্ডার',
    market_prices: 'বাজার দর', notifications: 'বিজ্ঞপ্তি', settings: 'সেটিংস', logout: 'লগ আউট', admin_view: 'অ্যাডমিন ভিউ',
    add_produce: 'ফসল যোগ করুন', edit: 'সম্পাদনা', delete: 'মুছুন', place_order: 'অর্ডার করুন', accept: 'গ্রহণ করুন', reject: 'প্রত্যাখ্যান',
    track_order: 'অর্ডার ট্র্যাক করুন', search: 'খুঁজুন', quantity: 'পরিমাণ', price: 'দাম', available: 'পাওয়া যাচ্ছে', low_stock: 'কম মজুত',
    sold_out: 'শেষ', earnings: 'আয়', pending_orders: 'অপেক্ষমাণ অর্ডার', completed_orders: 'সম্পন্ন অর্ডার',
    total_produce: 'মোট ফসল', active_orders: 'চলমান অর্ডার', total_spent: 'মোট খরচ', available_produce: 'উপলব্ধ ফসল',
    recent_orders: 'সাম্প্রতিক অর্ডার', route: 'রুট', home: 'হোম', profile: 'প্রোফাইল', farmer: 'কৃষক', buyer: 'ক্রেতা',
    order_placed: 'অর্ডার হয়ে গেছে! কৃষককে জানানো হয়েছে।', mark_preparing: 'প্রস্তুতি শুরু', mark_out_for_delivery: 'ডেলিভারির পথে',
    mark_delivered: 'পৌঁছে গেছে', asking_price: 'চাওয়া দাম', market_price: 'বাজার দর', view_all: 'সব দেখুন',
    all_crops: 'সব ফসল', all_locations: 'সব জায়গা', max_price: 'সর্বোচ্চ দাম', only_available: 'শুধু মজুত আছে',
    list_view: 'তালিকা', map_view: 'মানচিত্র', forgot_password: 'পাসওয়ার্ড ভুলে গেছেন?', reset_password: 'পাসওয়ার্ড রিসেট',
    new_password: 'নতুন পাসওয়ার্ড', login: 'লগ ইন', signup: 'অ্যাকাউন্ট খুলুন',
    status_placed: 'অর্ডার হয়েছে', status_accepted: 'গৃহীত', status_rejected: 'প্রত্যাখ্যাত', status_preparing: 'প্রস্তুত হচ্ছে',
    status_out_for_delivery: 'ডেলিভারির পথে', status_delivered: 'পৌঁছে গেছে',
  },
  hi: {
    dashboard: 'डैशबोर्ड', my_produce: 'मेरी उपज', browse_produce: 'उपज देखें', orders: 'ऑर्डर', my_orders: 'मेरे ऑर्डर',
    market_prices: 'बाज़ार भाव', notifications: 'सूचनाएं', settings: 'सेटिंग्स', logout: 'लॉग आउट', admin_view: 'एडमिन व्यू',
    add_produce: 'उपज जोड़ें', edit: 'संपादित करें', delete: 'हटाएं', place_order: 'ऑर्डर करें', accept: 'स्वीकार करें', reject: 'अस्वीकार करें',
    track_order: 'ऑर्डर ट्रैक करें', search: 'खोजें', quantity: 'मात्रा', price: 'कीमत', available: 'उपलब्ध', low_stock: 'कम स्टॉक',
    sold_out: 'बिक गया', earnings: 'कमाई', pending_orders: 'लंबित ऑर्डर', completed_orders: 'पूर्ण ऑर्डर',
    total_produce: 'कुल उपज', active_orders: 'सक्रिय ऑर्डर', total_spent: 'कुल खर्च', available_produce: 'उपलब्ध उपज',
    recent_orders: 'हाल के ऑर्डर', route: 'रूट', home: 'होम', profile: 'प्रोफ़ाइल', farmer: 'किसान', buyer: 'खरीदार',
    order_placed: 'ऑर्डर हो गया! किसान को सूचित कर दिया गया है।', mark_preparing: 'तैयारी शुरू करें', mark_out_for_delivery: 'डिलीवरी के लिए निकला',
    mark_delivered: 'पहुंच गया', asking_price: 'मांगी गई कीमत', market_price: 'बाज़ार भाव', view_all: 'सभी देखें',
    all_crops: 'सभी फसलें', all_locations: 'सभी स्थान', max_price: 'अधिकतम कीमत', only_available: 'केवल स्टॉक में',
    list_view: 'सूची', map_view: 'नक्शा', forgot_password: 'पासवर्ड भूल गए?', reset_password: 'पासवर्ड रीसेट',
    new_password: 'नया पासवर्ड', login: 'लॉग इन', signup: 'खाता बनाएं',
    status_placed: 'ऑर्डर किया गया', status_accepted: 'स्वीकृत', status_rejected: 'अस्वीकृत', status_preparing: 'तैयार हो रहा है',
    status_out_for_delivery: 'डिलीवरी के लिए निकला', status_delivered: 'पहुंच गया',
  },
};

const LangContext = createContext({ lang: 'en', change: () => {}, t: (k) => k });

export function LangProvider({ children }) {
  const [lang, setLang] = useState(localStorage.getItem('ks_lang') || 'en');
  const change = (l) => { setLang(l); localStorage.setItem('ks_lang', l); };
  const t = (k) => (T[lang] && T[lang][k]) || T.en[k] || k;
  return <LangContext.Provider value={{ lang, change, t }}>{children}</LangContext.Provider>;
}

export const useLang = () => useContext(LangContext);

export function LangSelector() {
  const { lang, change } = useLang();
  return <div className="lang-select" data-testid="language-selector">{LANGS.map(([c, l]) =>
    <button key={c} data-testid={`lang-${c}`} className={lang === c ? 'active' : ''} onClick={() => change(c)}>{l}</button>)}</div>;
}
