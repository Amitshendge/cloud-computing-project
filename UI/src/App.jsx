import React, { useState, useRef } from "react";
import ImgCutter from "../pages/ImgCutter";
import AboutUs from "../pages/AboutUs";
import ContactUs from "../pages/ContactUs";
import "./index.css";
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import ImgOCR from "../pages/ImgOCR";


function ImageUpload() {
  
  return (
    <Router>
      <Routes>
        <Route path="/" element={<ImgCutter />} />
        <Route path="/hello" element={<ImgOCR />} />
        <Route path="/AboutUs" element={<AboutUs />} />
        <Route path="/ContactUs" element={<ContactUs />} />
      </Routes>
    </Router>
  )
}

export default ImageUpload;