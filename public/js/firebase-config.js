// ⚠️ Reemplaza estos valores con los de tu proyecto Firebase
// ⚠️ Completa apiKey, messagingSenderId y appId desde la consola de Firebase:
// https://console.firebase.google.com/project/bot-controlelectoral/settings/general
const firebaseConfig = {
    apiKey: "AIzaSyD254wQ383t4za9bRTExziGAQ5hxFIJG4w",
    authDomain: "bot-controlelectoral-afddf.firebaseapp.com",
    databaseURL: "https://bot-controlelectoral-afddf-default-rtdb.firebaseio.com",
    projectId: "bot-controlelectoral-afddf",
    storageBucket: "bot-controlelectoral-afddf.firebasestorage.app",
    messagingSenderId: "662506770399",
    appId: "1:662506770399:web:63cb0e7965be98301c7e6a",
    measurementId: "G-FHWY96H6ML",
};

firebase.initializeApp(firebaseConfig);
const database = firebase.database();
