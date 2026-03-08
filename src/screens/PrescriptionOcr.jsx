import React, { useState, useRef } from 'react';
import NavbarDashboard from '../components/NavbarDashboard';
import Footer from '../components/Footer';
import { useParams } from 'react-router-dom';
import { FaCamera, FaUpload } from 'react-icons/fa';

export default function PrescriptionOcr() {
  const { hospital_id } = useParams();
  const [hospitalName, setHospitalName] = useState('');
  const [imageFile, setImageFile] = useState(null);
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [extractedData, setExtractedData] = useState(null);
  
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [isCameraActive, setIsCameraActive] = useState(false);

  const startCamera = async () => {
    setIsCameraActive(true);
    setErrorMessage('');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    } catch (err) {
      console.error("Error accessing camera:", err);
      setErrorMessage("Could not access the camera. Please ensure permissions are granted in your browser settings.");
      setIsCameraActive(false);
    }
  };

  const capturePhoto = () => {
    if (videoRef.current && canvasRef.current) {
      const context = canvasRef.current.getContext('2d');
      canvasRef.current.width = videoRef.current.videoWidth;
      canvasRef.current.height = videoRef.current.videoHeight;
      context.drawImage(videoRef.current, 0, 0, canvasRef.current.width, canvasRef.current.height);
      
      canvasRef.current.toBlob((blob) => {
        const file = new File([blob], "captured_prescription.jpg", { type: "image/jpeg" });
        setImageFile(file);
        setExtractedData(null);
        setSuccessMessage('');
        setErrorMessage('');
        stopCamera();
      }, 'image/jpeg');
    }
  };

  const stopCamera = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      const tracks = videoRef.current.srcObject.getTracks();
      tracks.forEach(track => track.stop());
    }
    setIsCameraActive(false);
  };

  const handleFileChange = (e) => {
    setImageFile(e.target.files[0]);
    // Reset data when a new file is chosen
    setExtractedData(null);
    setSuccessMessage('');
    setErrorMessage('');
  };

  const handleSubmit = async () => {
    if (!imageFile) {
        setErrorMessage('Please select an image file first.');
        return;
    }

    setLoading(true);
    setErrorMessage('');
    
    try {
      const formData = new FormData();
      formData.append('image_file', imageFile);

      const response = await fetch(`${process.env.REACT_APP_API_URL}/prescription_ocr?hospital_id=${hospital_id}`, {
        method: 'POST',
        body: formData,
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
        }
      });

      const data = await response.json();
      if (response.ok) {
        setSuccessMessage(data.message);
        setExtractedData(data.extracted_data);
      } else {
        setSuccessMessage('');
        setErrorMessage(data.error || 'Error extracting prescription data.');
      }
    } catch (error) {
      console.error('Error uploading image:', error);
      setSuccessMessage('');
      setErrorMessage('Network error. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <NavbarDashboard hospitalName={hospitalName} />
      <div className="container mt-5 mb-5">
        <h2>Scan Prescription</h2>
        <div className="card p-4 shadow-sm mt-4 custom-card">
          <div className="mb-3">
            <label className="form-label font-weight-bold d-block pb-2 border-bottom">
              Choose an option:
            </label>
            <div className="d-flex gap-3 mt-3">
              <div>
                <button type="button" onClick={startCamera} className="btn btn-outline-primary d-flex align-items-center mb-0">
                  <FaCamera className="me-2"/> Capture Photo
                </button>
              </div>
              <div>
                <label htmlFor="uploadImage" className="btn btn-outline-secondary d-flex align-items-center mb-0">
                  <FaUpload className="me-2"/> Upload File
                </label>
                <input
                  type="file"
                  id="uploadImage"
                  accept="image/*"
                  onChange={handleFileChange}
                  className="d-none"
                />
              </div>
            </div>
            {isCameraActive && (
              <div className="mt-3 text-center bg-dark p-3 rounded">
                <video ref={videoRef} autoPlay playsInline style={{ width: '100%', maxWidth: '500px', borderRadius: '8px', border: '2px solid #fff' }}></video>
                <div className="mt-3 d-flex justify-content-center gap-3">
                  <button type="button" className="btn btn-success" onClick={capturePhoto}>Take Picture</button>
                  <button type="button" className="btn btn-danger" onClick={stopCamera}>Cancel</button>
                </div>
                <canvas ref={canvasRef} style={{ display: 'none' }}></canvas>
              </div>
            )}
            {imageFile && !isCameraActive && <p className="mt-3 mb-0 text-success fw-bold">Selected file: {imageFile.name}</p>}
          </div>
          <button className="btn btn-primary mt-3" onClick={handleSubmit} disabled={loading || !imageFile}>
            {loading ? 'Scanning & Extracting...' : 'Scan Prescription'}
          </button>
          
          {successMessage && <p className="mt-3 text-success fw-bold">{successMessage}</p>}
          {errorMessage && <p className="mt-3 text-danger fw-bold">{errorMessage}</p>}
        </div>

        {/* Display OCR Results neatly */}
        {extractedData && (
            <div className="card mt-4 p-4 shadow-sm bg-light">
                <h4 className="text-secondary border-bottom pb-2">Extracted Data</h4>
                <div className="row mt-3">
                    <div className="col-md-4">
                        <p><strong>Patient Name:</strong> {extractedData.PATIENT_NAME || 'N/A'}</p>
                    </div>
                    <div className="col-md-4">
                        <p><strong>Doctor Name:</strong> {extractedData.DOCTOR_NAME || 'N/A'}</p>
                    </div>
                    <div className="col-md-4">
                        <p><strong>Date:</strong> {extractedData.DATE || 'N/A'}</p>
                    </div>
                </div>

                <h5 className="mt-4 text-secondary">Medicines</h5>
                {extractedData.MEDICINES && extractedData.MEDICINES.length > 0 ? (
                    <table className="table table-bordered table-striped mt-2">
                        <thead className="table-dark">
                            <tr>
                                <th>Name</th>
                                <th>Dosage</th>
                                <th>Frequency</th>
                                <th>Duration</th>
                            </tr>
                        </thead>
                        <tbody>
                            {extractedData.MEDICINES.map((med, index) => (
                                <tr key={index}>
                                    <td>{med.NAME || '-'}</td>
                                    <td>{med.DOSAGE || '-'}</td>
                                    <td>{med.FREQUENCY || '-'}</td>
                                    <td>{med.DURATION || '-'}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                ) : (
                    <p className="text-muted fst-italic">No medicines detected.</p>
                )}
                
                {/* Raw JSON Debug View */}
                <div className="mt-4">
                    <button className="btn btn-sm btn-outline-secondary" type="button" data-bs-toggle="collapse" data-bs-target="#rawJson" aria-expanded="false" aria-controls="rawJson">
                        Toggle Raw JSON View
                    </button>
                    <div className="collapse mt-2" id="rawJson">
                        <pre className="bg-dark text-light p-3 rounded" style={{fontSize: '14px'}}>
                            {JSON.stringify(extractedData, null, 2)}
                        </pre>
                    </div>
                </div>
            </div>
        )}
      </div>
      <Footer />
    </div>
  );
}
