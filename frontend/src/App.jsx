import { useState, useEffect } from 'react';
import './App.css';

// We'll define the three restaurant names as per the spec (we don't know the actual names, so we'll use placeholders)
const RESTAURANTS = ['Restaurant A', 'Restaurant B', 'Restaurant C'];

function App() {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [selectedEntryId, setSelectedEntryId] = useState(null);
  const [editDescription, setEditDescription] = useState('');
  const [descriptionPromptOpen, setDescriptionPromptOpen] = useState(false);
  const [filterRestaurant, setFilterRestaurant] = useState('all');
  const [searchTicket, setSearchTicket] = useState('');

  // Fetch entries from the backend
  const fetchEntries = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/entries');
      if (!response.ok) {
        throw new Error(`Failed to fetch entries: ${response.status}`);
      }
      const data = await response.json();
      setEntries(data);
    } catch (err) {
      setError(err.message);
      setEntries([]);
    } finally {
      setLoading(false);
    }
  };

  // Upload images
  const handleUpload = async (files) => {
    setUploadLoading(true);
    setUploadError(null);
    const formData = new FormData();
    for (const file of files) {
      formData.append('files', file);
    }
    try {
      const response = await fetch('/upload', {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) {
        throw new Error(`Upload failed: ${response.status}`);
      }
      // Assuming the response returns the uploaded entries
      const data = await response.json();
      setEntries(prev => [...prev, ...data]); // Append new entries
    } catch (err) {
      setUploadError(err.message);
    } finally {
      setUploadLoading(false);
    }
  };

  // Update description of an entry
  const handleDescriptionSave = async () => {
    if (selectedEntryId === null) return;
    try {
      const response = await fetch(`/entries/${selectedEntryId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ description: editDescription }),
      });
      if (!response.ok) {
        throw new Error(`Failed to save description: ${response.status}`);
      }
      const updatedEntry = await response.json();
      // Update the entry in our state
      setEntries(prev =>
        prev.map(entry =>
          entry.id === updatedEntry.id ? updatedEntry : entry
        )
      );
      setDescriptionPromptOpen(false);
      setSelectedEntryId(null);
      setEditDescription('');
    } catch (err) {
      alert(`Error saving description: ${err.message}`);
    }
  };

  // Export CSV
  const handleExportCSV = async () => {
    try {
      const response = await fetch('/export');
      if (!response.ok) {
        throw new Error(`Export failed: ${response.status}`);
      }
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'til_entries.csv';
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert(`Error exporting CSV: ${err.message}`);
    }
  };

  // Load entries on component mount
  useEffect(() => {
    fetchEntries();
  }, []);

  // Filter entries based on restaurant and ticket number search
  const filteredEntries = entries.filter(entry => {
    const matchesRestaurant =
      filterRestaurant === 'all' || entry.restaurant === filterRestaurant;
    const matchesTicket = entry.ticket_number
      .toLowerCase()
      .includes(searchTicket.toLowerCase());
    return matchesRestaurant && matchesTicket;
  });

  // Determine if any row needs description (for visual flagging)
  const getRowStatus = (entry) => {
    if (!entry.description || entry.description.trim() === '') {
      return 'needs-description';
    }
    return entry.status.toLowerCase().includes('matched')
      ? 'matched'
      : 'unmatched';
  };

  // Open description prompt for an entry
  const openDescriptionPrompt = (entry) => {
    setSelectedEntryId(entry.id);
    setEditDescription(entry.description || '');
    setDescriptionPromptOpen(true);
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>TIL SYSTEM</h1>
      </header>
      <main>
        {!loading && entries.length === 0 && uploadLoading === 0 ? (
          <p className="empty-state">No bills uploaded yet. Upload images to get started.</p>
        ) : null}
        {loading && entries.length === 0 ? (
          <p className="loading-state">Loading entries...</p>
        ) : null}
        {error && entries.length === 0 ? (
          <p className="error-state">Error: {error}</p>
        ) : null}
        <div className="upload-section">
          <h2>Upload Bill Images</h2>
          <input
            type="file"
            accept="image/*"
            multiple
            onChange={(e) => {
              const files = Array.from(e.target.files);
              if (files.length > 0) {
                handleUpload(files);
                e.target.value = ''; // Reset input
              }
            }}
            disabled={uploadLoading}
          />
          {uploadLoading && <p className="upload-progress">Uploading...</p>}
          {uploadError && <p className="upload-error">Upload error: {uploadError}</p>}
        </div>
        <div className="table-section">
          <h2>Bill Entries</h2>
          <div className="toolbar">
            <div className="filter-search">
              <label htmlFor="restaurant-filter">Restaurant:</label>
              <select
                id="restaurant-filter"
                value={filterRestaurant}
                onChange={(e) => setFilterRestaurant(e.target.value)}
              >
                <option value="all">All</option>
                {RESTAURANTS.map(rest => <option key={rest} value={rest}>{rest}</option>)}
              </select>
              <label htmlFor="ticket-search">Ticket #:</label>
              <input
                id="ticket-search"
                type="text"
                value={searchTicket}
                onChange={(e) => setSearchTicket(e.target.value)}
                placeholder="Search ticket number"
              />
            </div>
            <button
              onClick={handleExportCSV}
              disabled={loading || entries.length === 0}
            >
              Export CSV
            </button>
          </div>
          {loading && entries.length > 0 ? (
            <p className="loading-state">Updating entries...</p>
          ) : null}
          <table className="entries-table">
            <thead>
              <tr>
                <th>Restaurant</th>
                <th>Ticket Number</th>
                <th>Discrepancy Type</th>
                <th>Thumbnail</th>
                <th>Description</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {filteredEntries.length === 0 ? (
                <tr>
                  <td colSpan="6" className="empty-table">
                    No entries match the current filters.
                  </td>
                </tr>
              ) : (
                filteredEntries.map((entry) => (
                  <tr
                    key={entry.id}
                    className={`entry-row ${getRowStatus(entry)}`}
                    onClick={
                      !entry.description || entry.description.trim() === ''
                        ? () => openDescriptionPrompt(entry)
                        : undefined
                    }
                  >
                    <td>{entry.restaurant}</td>
                    <td>{entry.ticket_number}</td>
                    <td>
                      <span className={`badge badge-${entry.discrepancy_type}`}>
                        {entry.discrepancy_type}
                      </span>
                    </td>
                    <td>
                      {entry.thumbnail ? (
                        <img
                          src={entry.thumbnail}
                          alt={`Thumbnail of ${entry.ticket_number}`}
                          className="thumbnail"
                        />
                      ) : (
                        <span className="no-thumbnail">No image</span>
                      )}
                    </td>
                    <td className="description-cell">
                      {entry.description || (
                        <span className="missing-description">
                          Click to add description
                        </span>
                      )}
                    </td>
                    <td>
                      <span className={`status-badge ${getRowStatus(entry)}`}>
                        {entry.status}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </main>
      {/* Description Prompt Modal */}
      {descriptionPromptOpen && selectedEntryId !== null && (
        <div className="modal-backdrop" onClick={() => {
          setDescriptionPromptOpen(false);
          setSelectedEntryId(null);
          setEditDescription('');
        }}>
          <div className="modal-content">
            <h2>Add Description</h2>
            {/* Find the selected entry to show its thumbnail */}
            {entries.map(entry => {
              if (entry.id === selectedEntryId) {
                return (
                  <div key={entry.id} className="modal-image">
                    <img
                      src={entry.thumbnail}
                      alt={`Bill for ticket ${entry.ticket_number}`}
                    />
                  </div>
                );
              }
              return null;
            })}
            <textarea
              placeholder="Enter description of the bill..."
              rows={4}
              value={editDescription}
              onChange={(e) => setEditDescription(e.target.value)}
            />
            <div className="modal-actions">
              <button
                onClick={() => {
                  setDescriptionPromptOpen(false);
                  setSelectedEntryId(null);
                  setEditDescription('');
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleDescriptionSave}
                disabled={!editDescription.trim()}
              >
                Save
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;