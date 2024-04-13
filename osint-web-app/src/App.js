import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { MultiSelect } from "react-multi-select-component";
import './App.css';

const options = [
  { label: "theHarvester", value: "theHarvester" },
  { label: "Amass", value: "Amass" }
];

function App() {
  const [domain, setDomain] = useState('');
  const [tools, setTools] = useState([]);
  const [loading, setLoading] = useState(false);
  const [scanDetails, setScanDetails] = useState(null);
  const [showResultsModal, setShowResultsModal] = useState(false);
  const [successScans, setSuccessScans] = useState([]);
  const [successScanIds, setSuccessScanIds] = useState([]);

  useEffect(() => {
    // Fetch success scans IDs from LocalStorage when component mounts
    const savedIds = localStorage.getItem('successScanIds');
    if (savedIds) {
      setSuccessScanIds(JSON.parse(savedIds));
      // Fetch all scans associated with successScanIds
      handleGetAllScans(JSON.parse(savedIds));
    }
  }, []);

  const handleScan = async () => {
    if (tools.length === 0) return;
    const toolsArray = tools.map(tool => tool.value);
    try {
      setLoading(true);
      const response = await axios.post('http://localhost:8000/scan', {
        domain,
        toolsArray 
      });

      const { id, results, start_time, end_time } = response.data;
      const newScan = {
        id,
        domain,
        start_time,
        end_time,
        results,
        toolsArray
      };

      setSuccessScans(prevState => [...prevState, newScan]);
      setSuccessScanIds(prevIds => [...prevIds, id]); // Save scan ID to successScanIds
      const newScansIds =[...successScanIds ,id]
      localStorage.setItem('successScanIds', JSON.stringify(newScansIds)); // Save to LocalStorage

      setScanDetails(newScan);
      setShowResultsModal(true);
    } catch (error) {
      console.error('Error initiating scan:', error);
      
      //of course should style custom alert .
      alert('Error initiating scan. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const handleGetAllScans = async (scanIds) => {
    try {
      setLoading(true);
      const response = await axios.get('http://localhost:8000/scan', {
        params: {
          scan_ids:  JSON.stringify(scanIds) 
        }
      });
  
      const allScans = response.data;
      const scanArrays = [];
      const successIds = []
      if(typeof allScans === 'object'){
        for(const [key,value] of Object.entries(allScans)){ 
          scanArrays.push(value);
          successIds.push(key);
        }
        setSuccessScans(scanArrays)
        setSuccessScanIds(successIds);
      }
      // Handle all scans as needed
    } catch (error) {
      console.error('Error fetching all scans:', error);

      //of course should style custom alert .
      alert('Error fetching scans.');
    } finally {
      setLoading(false);
    }
  };

  const handleShowResultsModal = (id) => {
    const selectedScan = successScans.find(scan => scan.id === id);
    if (selectedScan) {
      selectedScan.id = id;
      setScanDetails(selectedScan);
      // Fetch results associated with the selected scan ID and set them to scanResults state
      // You need to implement the logic to fetch scan results based on scan ID
      setShowResultsModal(true);
    }
  };

  const handleExportToExcel = async () => {
    console.log('export to excel' ,scanDetails);
    try {
      const response = await axios.get(`http://localhost:8000/export/${scanDetails.id}`, {
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `scan_results_for_${scanDetails?.domain}.xlsx`);
      document.body.appendChild(link);
      link.click();
      window.URL.revokeObjectURL(url);

    } catch (error) {
      alert('Error exporting to Excel. Please try again.');
      console.error('Error exporting to Excel:', error);
    }
  };

  return (
    <div className="container">
      <h1 className="title">OSINT Web Application</h1>
      <div className="input-container">
        <input
          type="text"
          value={domain}
          onChange={(e) => setDomain(e.target.value)}
          placeholder="Enter domain..."
          className="input-field"
        />
        <MultiSelect
          options={options}
          value={tools}
          onChange={setTools}
          labelledBy="Select"
          className='select-field'
          hasSelectAll={false}
          disableSearch={true}
          ClearSelectedIcon={null}
          overrideStrings={{
            "allItemsAreSelected":"All tools are selected",
          }}
        />
        <button onClick={handleScan} disabled={loading || tools.length === 0} className="scan-button">
          {loading ? 'Scanning...' : 'Scan'}
        </button>
      </div>
      <div className="scan-cards">
        {successScans.map((scan, index) => (
          <div key={index} className="scan-card">
            <h2>Scan Details</h2>
            <div>
            <p><strong>Domain:</strong> {scan.domain}</p>
            <p><strong>Tools:</strong> {scan?.toolsArray?.join(", ")}</p>
            <p><strong>Start Time:</strong> {scan.start_time}</p>
            <p><strong>End Time:</strong> {scan.end_time}</p>
            </div>
            <button onClick={() => handleShowResultsModal(scan.id)}>Display Results</button>
          </div>
        ))}
      </div>

      {/* Modal for displaying scan results */}
      {showResultsModal && (
        <div className="modal">
          <div className="modal-content">
            <div className="modal-header" >
              <h2>Scan Results for {scanDetails?.domain}</h2>
              <span className="close" onClick={() => setShowResultsModal(false)}>&times;</span>
            </div>
            <div className='modal-details'>
            <h3>Tools: <span>{scanDetails?.toolsArray?.join(", ")}</span></h3>
            </div>
            <div className='modal-details'> 
              <h3>Start:<span>{scanDetails?.start_time}</span></h3>
              <h3>End:<span>{scanDetails?.end_time}</span></h3>
            </div>
            <div className="modal-result-container">
              {scanDetails?.results? (
                <ul>
                  {Object.entries(scanDetails.results).map(([key, data]) => (
                    <li key={key}>
                      <h2>{key}</h2>
                      <ul>
                        {data.map((item, index) => (
                          <li className='modal-data-item' key={`${key}-${item}-${index}`}>
                            <strong>{item}</strong>
                          </li>
                        ))}
                      </ul>
                    </li>
                  ))}
                </ul>
              ) : (
                <p>No results found.</p>
              )}
            </div>
            {/* Button to export scan results to Excel */}
            <button className='export-to-excel-button' onClick={handleExportToExcel}>Export to Excel</button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
