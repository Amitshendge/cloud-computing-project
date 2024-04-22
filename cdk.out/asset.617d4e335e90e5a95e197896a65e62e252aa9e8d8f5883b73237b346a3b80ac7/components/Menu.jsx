import React from 'react';
import "../src/index.css";

const Menu = () => {
  return (
    <nav className="menu">
      <ul>
        <li><a href="/">Home</a></li>
        <li>
          Image Functions
          <ul>
            <li><a href="/">Image Cutter</a></li>
            <li><a href="/hello">Image OCR</a></li>
          </ul>
        </li>
        {/* <li>
          PDF Functions
          <ul>
            <li><a href="/pdf-to-img">PDF to IMG</a></li>
            <li><a href="/pdf-ocr">PDF OCR</a></li>
          </ul>
        </li> */}
        <li><a href="/AboutUs">About Us</a></li>
        <li><a href="/ContactUs">Contact Us</a></li>
      </ul>
    </nav>
  );
};

export default Menu;
