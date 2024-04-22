import React, { useState, useRef } from "react";
import "../src/index.css";
import Axios from "axios";
import Spinner from "../components/Spinner";
import Menu from "../components/Menu";
import Footer from "../components/Footer";
import { Link } from 'react-router-dom';
import my_file2 from '../my_file2.json';

var currentTime_id = Date.now()
var file;
const api_base_url = my_file2.REACT_APP_api_base_url
const func_url_yolo = my_file2.REACT_APP_func_url_yolo
const ImgCutter = () => {
  const [image, setImage] = useState(null);
  const [Uploaded, setUploaded] = useState(false);
  const [Processed, setProcessed] = useState(false);
  const [loading, setLoading] = useState(false);

  var [CropedImages, setCropedImages] = useState();
  const hiddenFileInput = useRef(null);
  var ctx;

  const handleOnchangeImage = (event) => {
    file = event.target.files[0];
    handleImageChange(null);
  }

  function handleImageChange(crop_dim) {
    const imgname = file.name;
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onloadend = () => {
      const img = new Image();
      img.src = reader.result;
      img.onload = () => {
        const canvas = document.createElement("canvas");
        const maxSize = Math.max(img.width, img.height);
        canvas.width = maxSize;
        canvas.height = maxSize;
        ctx = canvas.getContext("2d");
        ctx.drawImage(
          img,
          (maxSize - img.width) / 2,
          (maxSize - img.height) / 2
        );
        console.log(crop_dim);
          if (crop_dim){
        ctx.strokeStyle = 'red';
        ctx.lineWidth = 5;
        crop_dim.forEach(([upperLower, leftRight]) => {
          const [upper, lower] = upperLower;
          const [left, right] = leftRight;
          ctx.strokeRect(left, upper, right - left, lower - upper);
        });}
        else{
          setProcessed(false);
          setUploaded(false);
        }

        canvas.toBlob(
          (blob) => {
            const file = new File([blob], imgname, {
              type: "image/png",
              lastModified: Date.now(),
            });

            console.log(file);
            setImage(file);
          },
          "image/jpeg",
          0.8
        );
      };
    };
  };

  const handleDownloadButtonClick = async () => {
    setLoading(true);
    console.log("Started Downloading");

    Axios.post(`${api_base_url}/image_edit_cv2`, CropedImages
    )
    .then(response => {
      window.open(response.data.body.download_url);
      setLoading(false);
  })
    .catch(error => {
      console.log(error);
    });
  }

  const handleDownloadSampleButtonClick = async () => {
    setLoading(true);
    console.log("Started Downloading");

    Axios.get(`${api_base_url}/generate_presigned_download`, {params:{key: 'test_images/all_images.jpg'}}
    )
    .then(response => {
      window.open(response.data.body.download_url);
      setLoading(false);
  })
    .catch(error => {
      console.log(error);
    });
  }

  const handleStartProcessButtonClick = async () => {
    setLoading(true);
    console.log("Started Processing");
    const params = {
      key: `uploaded_raw_images/${currentTime_id}/`+image.name,
    };
    
    Axios.get(func_url_yolo, {
      params,
    })
    .then(response => {
      console.log(response.data['output']);
      const boxCoordinates = JSON.parse(response.data['output']);
      params['crop_dim'] = boxCoordinates;
      setCropedImages(params)
      setProcessed(true);
      handleImageChange(boxCoordinates);
      setLoading(false);
    })
    .catch(error => {
      console.log(error);
    });
  }
  const handleUploadButtonClick_dummy = async () => {
    try{
      image? setLoading(true):alert("Please select file to upload.");
      const response = await Axios.get(`${api_base_url}/generate_presigned_upload`, {
        params: {
          key: `uploaded_raw_images/${currentTime_id}/`+image.name,
        },
      })
      const res = response.data;
      var bodyFormData = new FormData();
      Object.keys(res.fields).forEach(key => {
        bodyFormData.append(key, res.fields[key]);
      });

      bodyFormData.append('file', image);
      const upload = await Axios.post(res['url'], bodyFormData)
      alert("File uploaded successfully.");
      setUploaded(true);
      setLoading(false);
    }
    catch (err) {
      console.log(err);
    }
      
  };
  
  const handleClick = (event) => {
    hiddenFileInput.current.click();
  };

  return (
    <div className="image-upload-container">
      <div className="box-decoration">
        <label htmlFor="image-upload-input" className="image-upload-label">
          {image ? image.name : "Choose an image"}
        </label>
        <div onClick={handleClick} style={{ cursor: "pointer" }}>
          {image ? (
            <img src={URL.createObjectURL(image)} alt="upload image" className="img-display-after" />
          ) : (
            <img src="./assets/photo.png" alt="upload image" className="img-display-before" />
          )}

          <input
            id="image-upload-input"
            type="file"
            onChange={handleOnchangeImage}
            ref={hiddenFileInput}
            style={{ display: "none" }}
          />
        </div>
        <div>
          {loading ? <Spinner /> : <div>{/* Render your data here */}</div>}
        </div>
        <button
          className="image-upload-button"
          onClick={Processed ? handleDownloadButtonClick:Uploaded ? handleStartProcessButtonClick:handleUploadButtonClick_dummy}
        >
          {Processed?"Download Croped Images":Uploaded ? "Start Process":"Upload"}
        </button>
      </div>
      <div>
      {image?undefined:<button className="sample-image-button" onClick={handleDownloadSampleButtonClick}>Download Sample Image</button>}
      </div>
    </div>
  );
}

export default ImgCutter;
