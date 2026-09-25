import { useState, useEffect } from 'react';
import './App.css';
import { uploadTicketScreenshotBatch, uploadDocketImageBatch } from './api/upload';
import { exportDockets, exportTickets, getDockets, getTickets } from './api/records';
import { updateEntry } from './api/entries';

// Fallback options shown only while the table is empty; real options are
// derived from the restaurant values the backend actually returns.
function App() {
  const [ticketUploadLoading, setTicketUploadLoading] = useState(false);
  const [ticketUploadError, setTicketUploadError] = useState(null);
  const [ticketUploadItems, setTicketUploadItems] = useState([]);
  const [showTicketData, setShowTicketData] = useState(false);
  const [ticketUploadData, setTicketUploadData] = useState([]);
  const [docketUploadLoading, setDocketUploadLoading] = useState(false);
  const [docketUploadError, setDocketUploadError] = useState(null);
  const [docketUploadItems, setDocketUploadItems] = useState([]);
  const [showDocketData, setShowDocketData] = useState(false);
  const [docketUploadData, setDocketUploadData] = useState([]);
  const [comparisonExcelFile, setComparisonExcelFile] = useState(null);
  const [comparisonLongSlipFile, setComparisonLongSlipFile] = useState(null);
  const activeView = 'tickets';
  const [tickets, setTickets] = useState([]);
  const [dockets, setDockets] = useState([]);
  const [selectedRestaurant, setSelectedRestaurant] = useState('');
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [comparisonCopyStatus, setComparisonCopyStatus] = useState('');
  const [recordsLoading, setRecordsLoading] = useState(false);
  const [recordsError, setRecordsError] = useState(null);
  // Description prompt state
  const [descriptionPromptOpen, setDescriptionPromptOpen] = useState(false);
  const [editingEntryId, setEditingEntryId] = useState(null);
  const [descriptionValue, setDescriptionValue] = useState('');
  const [descriptionSaving, setDescriptionSaving] = useState(false);
  const [descriptionError, setDescriptionError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setRecordsLoading(true);
    setRecordsError(null);
    Promise.all([getTickets(), getDockets()])
      .then(([ticketData, docketData]) => {
        if (cancelled) return;
        setTickets(ticketData);
        setDockets(docketData);
      })
      .catch((err) => {
        if (!cancelled) setRecordsError(err.message);
      })
      .finally(() => {
        if (!cancelled) setRecordsLoading(false);
      });
    return () => { cancelled = true; };
  }, []);

  // Helper function to get entry ID for a record (ticket or docket)
  const getEntryIdForRecord = async (record) => {
    if (activeView === 'dockets') {
      // For dockets, the API response includes the id field
      return record.id;
    } else {
      // For tickets, we need to find the associated entry by ticket_number
      try {
        const entries = await getEntries({ ticketNumber: record.ticket_id });
        if (entries.length > 0) {
          // Return the first entry's ID (ordered by created_at descending per getEntries)
          return entries[0].id;
        } else {
          // No entries found for this ticket
          throw new Error(`No entries found for ticket ${record.ticket_id}`);
        }
      } catch (err) {
        console.error(`Failed to get entry ID for ticket ${record.ticket_id}:`, err);
        throw err;
      }
    }
  };

  const handleTicketScreenshotUpload = async (files) => {
    setTicketUploadLoading(true);
    setTicketUploadError(null);
    const items = files.map((file, index) => ({
      id: `${file.name}-${file.lastModified}-${index}`,
      name: file.name,
      status: 'uploading',
      message: 'Parsing ticket screenshots...'
    }));
    setTicketUploadItems(items);

    try {
      const result = await uploadTicketScreenshotBatch(files);
      const failed = result.failed || [];
      const succeeded = result.succeeded || [];

      setTicketUploadItems(
        files.map((file, index) => {
          const failedItem = failed.find((item) => item.filename === file.name || item.original_filename === file.name);
          const successItem = succeeded.find((item) => item.original_filename === file.name);
          if (failedItem) {
            return { id: `${file.name}-${file.lastModified}-${index}`, name: file.name, status: 'error', message: failedItem.reason };
          }
          if (successItem) {
            return { id: `${file.name}-${file.lastModified}-${index}`, name: file.name, status: 'success', message: 'Saved successfully' };
          }
          return { id: `${file.name}-${file.lastModified}-${index}`, name: file.name, status: 'uploading', message: 'Queued' };
        })
      );
      if (failed.length > 0) {
        setTicketUploadError(`Some ticket screenshots failed: ${failed.map((item) => item.filename).join(', ')}`);
      }
      const refreshedTickets = await getTickets();
      setTickets(refreshedTickets);
      setTicketUploadData(refreshedTickets);
      setShowTicketData(true);
    } catch (err) {
      setTicketUploadItems(prev => prev.map(item => ({ ...item, status: 'error', message: err.message })));
      setTicketUploadError(err.message);
    } finally {
      setTicketUploadLoading(false);
    }
  };

  const handleDocketUpload = async (files) => {
    setDocketUploadLoading(true);
    setDocketUploadError(null);
    const items = files.map((file, index) => ({
      id: `${file.name}-${file.lastModified}-${index}`,
      name: file.name,
      status: 'uploading',
      message: 'Saving docket batch...'
    }));
    setDocketUploadItems(items);

    try {
      const result = await uploadDocketImageBatch(files);
      const failed = result.failed || [];
      const succeeded = result.succeeded || [];

      setDocketUploadItems(
        files.map((file, index) => {
          const failedItem = failed.find((item) => item.filename === file.name || item.original_filename === file.name);
          const successItem = succeeded.find((item) => item.original_filename === file.name);
          if (failedItem) {
            return { id: `${file.name}-${file.lastModified}-${index}`, name: file.name, status: 'error', message: failedItem.reason };
          }
          if (successItem) {
            return { id: `${file.name}-${file.lastModified}-${index}`, name: file.name, status: 'success', message: 'Saved successfully' };
          }
          return { id: `${file.name}-${file.lastModified}-${index}`, name: file.name, status: 'uploading', message: 'Queued' };
        })
      );
      if (failed.length > 0) {
        setDocketUploadError(`Some dockets failed to save: ${failed.map((item) => item.filename).join(', ')}`);
      }
      const refreshedDockets = await getDockets();
      setDockets(refreshedDockets);
      setDocketUploadData(refreshedDockets);
      setShowDocketData(true);
    } catch (err) {
      setDocketUploadItems(prev => prev.map(item => ({ ...item, status: 'error', message: err.message })));
      setDocketUploadError(err.message);
    } finally {
      setDocketUploadLoading(false);
    }
  };

  const recordRows = activeView === 'tickets' ? tickets : dockets;
  const restaurantOptions = [...new Set(tickets.map((ticket) => ticket.restaurant).filter(Boolean))].sort();
  const filteredTickets = selectedRestaurant
    ? tickets.filter((ticket) => ticket.restaurant === selectedRestaurant)
    : [];
  const filteredDockets = selectedRestaurant
    ? dockets.filter((docket) => docket.restaurant === selectedRestaurant)
    : [];

  const requireRestaurant = () => {
    if (!selectedRestaurant) {
      setTicketUploadError('Select a restaurant before uploading ticket screenshots.');
      return false;
    }
    return true;
  };

  const matchingDockets = selectedTicket
    ? dockets.filter((docket) => String(docket.order_number || '') === String(selectedTicket.ticket_id || '').match(/(\d+)$/)?.[1])
    : [];
  const selectedVoidItems = selectedTicket?.items?.filter((item) => item.is_void) || [];
  const comparisonMismatch = selectedTicket && (
    selectedVoidItems.length > 0 && matchingDockets.length === 0
    || matchingDockets.some((docket) => docket.discrepancy_type !== 'void')
  );

  const handleSelectTicket = (ticket) => {
    setSelectedTicket(ticket);
    setComparisonCopyStatus('');
  };

  const handleRecordsExport = async (view) => {
    try {
      if (view === 'tickets') await exportTickets();
      if (view === 'dockets') await exportDockets();
    } catch (err) {
      alert(`Error exporting parsed data: ${err.message}`);
    }
  };

  const handleCopyComparisonData = async () => {
    if (!selectedTicket) return;
    const structuredData = {
      ticket: {
        ticket_id: selectedTicket.ticket_id,
        restaurant: selectedTicket.restaurant,
        date: selectedTicket.date,
        ticket_total: selectedTicket.ticket_total,
        payment_status: selectedTicket.payment_status,
        items: selectedTicket.items?.map((item) => ({
          item: item.item,
          total: item.total,
          qty: item.qty,
          is_void: item.is_void
        })) || []
      },
      dockets: matchingDockets.map((docket) => ({
        order_number: docket.order_number,
        item: docket.item,
        discrepancy_type: docket.discrepancy_type,
        handwritten_reason: docket.description
      })),
      comparison_mismatch: Boolean(comparisonMismatch)
    };

    try {
      if (!navigator.clipboard) throw new Error('Clipboard access is not available in this browser.');
      await navigator.clipboard.writeText(JSON.stringify(structuredData, null, 2));
      setComparisonCopyStatus('Copied');
      window.setTimeout(() => setComparisonCopyStatus(''), 1800);
    } catch (err) {
      alert(`Failed to copy comparison data: ${err.message}`);
    }
  };

  const renderTicketTable = (rows, label) => (
    <div className="upload-data-table">
      <p className="eyebrow">{label}</p>
      <div className="table-scroll">
        <table className="entries-table parsed-table">
          <thead><tr>
            <th className="ticket-id-header">Ticket Number</th><th>Uploaded</th><th>Restaurant</th><th>Date</th><th>Terminal</th>
            <th>Table</th><th>Department</th><th>User</th><th>Payment Status</th><th>Status</th><th>Credit Card Amount</th><th>Items</th><th>Ticket Total</th><th>Grand Total</th><th>Charged</th>
          </tr></thead>
          <tbody>
            {rows.length === 0 ? <tr><td colSpan="15" className="empty-table">No parsed ticket screenshots yet.</td></tr> : rows.map((ticket) => {
              const statusClass = ticket.status === 'needs_description' ? 'needs-description-row' : '';
              return (
                <tr
                  key={ticket.ticket_id}
                  className={`ticket-select-row ${selectedTicket?.ticket_id === ticket.ticket_id ? 'selected-ticket-row' : ''} ${statusClass}`}
                  onClick={async () => {
                    if (ticket.status === 'needs_description') {
                      try {
                        const entryId = await getEntryIdForRecord(ticket);
                        setEditingEntryId(entryId);
                        setDescriptionValue(ticket.description || '');
                        setDescriptionPromptOpen(true);
                      } catch (err) {
                        setDescriptionError(`Failed to load entry for ticket ${ticket.ticket_id}: ${err.message}`);
                        setEditingEntryId(null);
                        setDescriptionValue('');
                        setDescriptionPromptOpen(true);
                      }
                    } else {
                      handleSelectTicket(ticket);
                    }
                  }}
                  tabIndex="0"
                  onKeyDown={async (event) => {
                    if (event.key === 'Enter') {
                      if (ticket.status === 'needs_description') {
                        try {
                          const entryId = await getEntryIdForRecord(ticket);
                          setEditingEntryId(entryId);
                          setDescriptionValue(ticket.description || '');
                          setDescriptionPromptOpen(true);
                        } catch (err) {
                          setDescriptionError(`Failed to load entry for ticket ${ticket.ticket_id}: ${err.message}`);
                          setEditingEntryId(null);
                          setDescriptionValue('');
                          setDescriptionPromptOpen(true);
                        }
                      } else {
                        handleSelectTicket(ticket);
                      }
                    }
                  }}
                >
                  <td className="ticket-id-cell"><strong>{ticket.ticket_id || 'Missing ticket ID'}</strong></td>
                  <td>{ticket.uploaded_at ? new Date(`${ticket.uploaded_at}Z`).toLocaleString() : '—'}</td>
                  <td>{ticket.restaurant || '—'}</td>
                  <td>{ticket.date || '—'}</td>
                  <td>{ticket.terminal || '—'}</td>
                  <td>{ticket.table || '—'}</td>
                  <td>{ticket.department || '—'}</td>
                  <td>{ticket.user || '—'}</td>
                  <td>{ticket.payment_status || '—'}</td>
                  <td className={`status-cell ${ticket.status}`}>{ticket.status || '—'}</td>
                  <td>{ticket.credit_card_amount || '—'}</td>
                  <td>{ticket.items?.length ? `${ticket.items.length} item${ticket.items.length === 1 ? '' : 's'}` : '—'}</td>
                  <td>{ticket.ticket_total || '—'}</td>
                  <td>{ticket.grand_total || '—'}</td>
                  <td>{ticket.charged || '—'}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );

  const renderDocketTable = (rows, label) => (
    <div className="upload-data-table">
      <p className="eyebrow">{label}</p>
      <div className="table-scroll">
        <table className="entries-table parsed-table">
          <thead><tr><th>Order No</th><th>Date</th><th>Time</th><th>Item</th><th>Discrepancy Type</th><th>Status</th><th>Handwritten Reason</th></tr></thead>
          <tbody>
            {rows.length === 0 ? <tr><td colSpan="7" className="empty-table">No parsed dockets yet.</td></tr> : rows.map((docket) => {
              const statusClass = docket.status === 'needs_description' ? 'needs-description-row' : '';
              return (
                <tr
                  key={docket.id}
                  className={`${docket.review_required ? 'parsed-review-row' : ''} ${statusClass}`}
                  onClick={async () => {
                    if (docket.status === 'needs_description') {
                      try {
                        const entryId = await getEntryIdForRecord(docket);
                        setEditingEntryId(entryId);
                        setDescriptionValue(docket.description || '');
                        setDescriptionPromptOpen(true);
                      } catch (err) {
                        setDescriptionError(`Failed to load entry for docket ${docket.order_number}: ${err.message}`);
                        setEditingEntryId(null);
                        setDescriptionValue('');
                        setDescriptionPromptOpen(true);
                      }
                    }
                  }}
                  tabIndex="0"
                  onKeyDown={async (event) => {
                    if (event.key === 'Enter' && docket.status === 'needs_description') {
                      try {
                        const entryId = await getEntryIdForRecord(docket);
                        setEditingEntryId(entryId);
                        setDescriptionValue(docket.description || '');
                        setDescriptionPromptOpen(true);
                      } catch (err) {
                        setDescriptionError(`Failed to load entry for docket ${docket.order_number}: ${err.message}`);
                        setEditingEntryId(null);
                        setDescriptionValue('');
                        setDescriptionPromptOpen(true);
                      }
                    }
                  }}
                >
                  <td><strong>{docket.order_number || '—'}</strong></td>
                  <td>{docket.date || '—'}</td>
                  <td>{docket.time || '—'}</td>
                  <td>{docket.item || '—'}</td>
                  <td><span className={`badge badge-${docket.discrepancy_type || 'unknown'}`}>{docket.discrepancy_type || 'unknown'}</span></td>
                  <td className={`status-cell ${docket.status}`}>{docket.status || '—'}</td>
                  <td className="handwritten-cell">{docket.description || '—'}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );

  return (
    <div className="app">
      <header className="app-header">
        <div className="brand-lockup">
          <div className="brand-mark">T</div>
          <div>
            <p className="eyebrow">Restaurant operations</p>
            <h1>TIL System</h1>
          </div>
        </div>
        <div className="header-meta">
          <span className="live-dot" />
          <span>Workspace active</span>
        </div>
      </header>
      <main className="app-main">
        <section className="welcome-row">
          <div>
            <p className="eyebrow">Daily reconciliation</p>
            <h2>Keep every bill accounted for.</h2>
            <p className="welcome-copy">Review discrepancies, add context, and keep your restaurant records moving.</p>
          </div>
          <div className="date-chip">Today <strong>{new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</strong></div>
        </section>

        <>

        <section className="restaurant-filter-section">
          <div>
            <p className="eyebrow">Step 1</p>
            <h2>Choose a restaurant</h2>
            <p className="filter-copy">Select the restaurant for this working day before adding screenshots and docket images.</p>
          </div>
          <label className="restaurant-filter-field">
            <span>Restaurant</span>
            <select value={selectedRestaurant} onChange={(event) => setSelectedRestaurant(event.target.value)}>
              <option value="">Select a restaurant</option>
              {restaurantOptions.map((restaurant) => <option key={restaurant} value={restaurant}>{restaurant}</option>)}
            </select>
          </label>
        </section>

        <section className="comparison-source-panel" aria-labelledby="comparison-source-title">
          <div className="comparison-source-copy">
            <p className="eyebrow">Comparison source</p>
            <h2 id="comparison-source-title">Choose a file to compare</h2>
            <p>Use an Excel file for structured data or a long bill slip image. File processing and comparison will be connected by the backend team.</p>
          </div>
          <div className="comparison-source-actions">
            <div className="comparison-source-control">
              <input
                id="comparison-excel-upload"
                className="file-picker"
                type="file"
                accept=".xls,.xlsx,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                onChange={(event) => {
                  const [file] = Array.from(event.target.files || []);
                  if (file) setComparisonExcelFile(file);
                  event.target.value = '';
                }}
              />
              <label className="source-upload-button" htmlFor="comparison-excel-upload">
                <span className="source-upload-button-icon">XLS</span>
                Upload Excel
              </label>
              <span className={`source-file-selection ${comparisonExcelFile ? 'has-file' : ''}`} title={comparisonExcelFile?.name || ''}>
                {comparisonExcelFile ? `Selected: ${comparisonExcelFile.name}` : 'Excel file (.xls, .xlsx)'}
              </span>
            </div>
            <div className="comparison-source-control">
              <input
                id="comparison-long-slip-upload"
                className="file-picker"
                type="file"
                accept="image/*"
                onChange={(event) => {
                  const [file] = Array.from(event.target.files || []);
                  if (file) setComparisonLongSlipFile(file);
                  event.target.value = '';
                }}
              />
              <label className="source-upload-button" htmlFor="comparison-long-slip-upload">
                <span className="source-upload-button-icon">IMG</span>
                Upload long bill slip
              </label>
              <span className={`source-file-selection ${comparisonLongSlipFile ? 'has-file' : ''}`} title={comparisonLongSlipFile?.name || ''}>
                {comparisonLongSlipFile ? `Selected: ${comparisonLongSlipFile.name}` : 'Long bill slip image'}
              </span>
            </div>
          </div>
        </section>

        <section className="bulk-upload-grid">
          <div className="upload-section bulk-panel">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Ticket screenshots</p>
                <h2>Upload screenshots in bulk</h2>
              </div>
              <span className="section-icon">IMG</span>
            </div>
            <label className={`upload-dropzone ${!selectedRestaurant ? 'upload-disabled' : ''}`} htmlFor="ticket-screenshot-upload">
              <span className="upload-icon">＋</span>
              <span className="upload-title">Select ticket screenshots</span>
              <span className="upload-hint">PNG, JPG or WEBP · Up to 30 screenshots</span>
              <span className="upload-button">Browse screenshots</span>
            </label>
            <input
              id="ticket-screenshot-upload"
              className="file-picker"
              type="file"
              accept="image/*"
              multiple
              onChange={(e) => {
                const files = Array.from(e.target.files);
                if (files.length > 0 && requireRestaurant()) {
                  handleTicketScreenshotUpload(files);
                  e.target.value = '';
                }
              }}
              disabled={ticketUploadLoading || !selectedRestaurant}
            />
            {ticketUploadLoading && <p className="upload-progress">Parsing ticket screenshots...</p>}
            {ticketUploadError && <p className="upload-error">{ticketUploadError}</p>}
            {ticketUploadItems.length > 0 && (
              <div className="upload-status-list" aria-live="polite">
                {ticketUploadItems.map(item => (
                  <div className={`upload-status-item ${item.status}`} key={item.id}>
                    <span className="upload-status-icon">{item.status === 'uploading' ? '...' : item.status === 'success' ? 'OK' : '!'}</span>
                    <span className="upload-file-name">{item.name}</span>
                    <span className="upload-file-message">{item.message}</span>
                  </div>
                ))}
              </div>
            )}
            {ticketUploadItems.some((item) => item.status === 'success') && (
              <button className="show-data-button" onClick={() => setShowTicketData((visible) => !visible)}>
                {showTicketData ? 'Hide data' : 'Show data'}
              </button>
            )}
            {showTicketData && ticketUploadData.filter((ticket) => ticket.restaurant === selectedRestaurant).length > 0 && renderTicketTable(ticketUploadData.filter((ticket) => ticket.restaurant === selectedRestaurant), 'Uploaded ticket data')}
          </div>

          <div className="upload-section bulk-panel">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Bulk docket</p>
                <h2>Discrepancy images</h2>
              </div>
              <span className="section-icon">IMG</span>
            </div>
            <label className={`upload-dropzone ${!selectedRestaurant ? 'upload-disabled' : ''}`} htmlFor="docket-upload">
              <span className="upload-icon">＋</span>
              <span className="upload-title">Choose docket batch</span>
              <span className="upload-hint">PNG, JPG or WEBP · Up to 30 images</span>
              <span className="upload-button">Browse images</span>
            </label>
            <input
              id="docket-upload"
              className="file-picker"
              type="file"
              accept="image/*"
              multiple
              onChange={(e) => {
                const files = Array.from(e.target.files);
                if (files.length > 0 && requireRestaurant()) {
                  handleDocketUpload(files);
                  e.target.value = '';
                }
              }}
              disabled={docketUploadLoading || !selectedRestaurant}
            />
            {docketUploadLoading && <p className="upload-progress">Saving dockets...</p>}
            {docketUploadError && <p className="upload-error">{docketUploadError}</p>}
            {docketUploadItems.length > 0 && (
              <div className="upload-status-list" aria-live="polite">
                {docketUploadItems.map(item => (
                  <div className={`upload-status-item ${item.status}`} key={item.id}>
                    <span className="upload-status-icon">{item.status === 'uploading' ? '...' : item.status === 'success' ? 'OK' : '!'}</span>
                    <span className="upload-file-name">{item.name}</span>
                    <span className="upload-file-message">{item.message}</span>
                  </div>
                ))}
              </div>
            )}
            {docketUploadItems.some((item) => item.status === 'success') && (
              <button className="show-data-button" onClick={() => {
                setShowDocketData((visible) => !visible);
              }}>
                {showDocketData ? 'Hide data' : 'Show data'}
              </button>
            )}
            {showDocketData && docketUploadData.length > 0 && selectedRestaurant && renderDocketTable(docketUploadData, 'Uploaded docket data')}
          </div>
        </section>
        <section id="records-section" className="parsed-record-section">
          <div className="section-heading table-heading">
            <div>
              <p className="eyebrow">Parsed data</p>
              <h2>Tickets and dockets <span className="entry-count">{tickets.length + dockets.length}</span></h2>
            </div>
            <button className="export-button" onClick={() => handleRecordsExport(activeView)} disabled={recordsLoading || recordRows.length === 0}>
              <span>↓</span> Export {activeView === 'tickets' ? 'tickets' : 'dockets'} CSV
            </button>
          </div>
          {recordsLoading && <p className="loading-state">Loading parsed {activeView}...</p>}
          {recordsError && <p className="error-state">Error: {recordsError}</p>}
          <div className="combined-record-tables">
            {activeView === 'tickets' ? renderTicketTable(filteredTickets, 'Ticket data') : renderDocketTable(filteredDockets, 'Docket data')}
          </div>
        </section>
        </>
        {selectedTicket && (
          <section className="comparison-view">
            <div className="section-heading comparison-heading">
              <div>
                <p className="eyebrow">Ticket comparison</p>
                <h2>{selectedTicket.ticket_id}</h2>
                <p className="comparison-copy">Compare the selected ticket against the docket discrepancy images for this order.</p>
              </div>
              <div className="button-group">
                <button className="show-data-button" onClick={() => handleSelectTicket(null)}>Back to tickets</button>
                <button className="show-data-button" onClick={handleCopyComparisonData}>{comparisonCopyStatus || 'Copy data'}</button>
              </div>
            </div>
            <div className={`comparison-result ${comparisonMismatch ? 'comparison-mismatch' : 'comparison-match'}`}>
              <strong>{comparisonMismatch ? 'Mismatch found' : 'No mismatch found'}</strong>
              <span>{comparisonMismatch ? 'Review the highlighted ticket or docket information.' : 'The selected ticket and docket evidence are aligned.'}</span>
            </div>
            <div className="comparison-grid">
              <article className="comparison-panel">
                <p className="eyebrow">Ticket row information</p>
                <dl className="comparison-details">
                  <dt>Restaurant</dt><dd>{selectedTicket.restaurant || '—'}</dd>
                  <dt>Date</dt><dd>{selectedTicket.date || '—'}</dd>
                  <dt>Ticket total</dt><dd>{selectedTicket.ticket_total || '—'}</dd>
                  <dt>Payment status</dt><dd>{selectedTicket.payment_status || '—'}</dd>
                </dl>
                <div className="comparison-items">
                  {selectedTicket.items?.map((item, index) => (
                    <div className={item.is_void ? 'comparison-item mismatch-highlight' : 'comparison-item'} key={`${selectedTicket.ticket_id}-${index}`}>
                      <strong>{item.item || 'Unnamed item'}</strong>
                      <span>{item.total || '—'} · Qty {item.qty || '—'}</span>
                      {item.is_void && <em>VOID</em>}
                    </div>
                  ))}
                </div>
              </article>
              <article className="comparison-panel">
                <p className="eyebrow">Bulk docket discrepancy images</p>
                {matchingDockets.length === 0 ? (
                  <div className="comparison-empty mismatch-highlight">No docket evidence matches order {selectedTicket.ticket_id.match(/(\d+)$/)?.[1] || '—'}.</div>
                ) : matchingDockets.map((docket) => (
                  <div className={`docket-comparison-card ${docket.discrepancy_type !== 'void' ? 'mismatch-highlight' : ''}`} key={docket.id}>
                    <div className="comparison-card-heading"><strong>Order {docket.order_number}</strong><span className="badge badge-void">{docket.discrepancy_type || 'unknown'}</span></div>
                    <p>{docket.item || 'Docket item not parsed'}</p>
                    <span>{docket.description || 'No handwritten reason captured'}</span>
                    {docket.image_filename && <small>{docket.image_filename}</small>}
                  </div>
                ))}
              </article>
            </div>
          </section>
        )}
        {/* Description Prompt Modal */}
        {descriptionPromptOpen && (
          <div className="description-modal-backdrop" onClick={() => {
            if (descriptionPromptOpen) {
              setDescriptionPromptOpen(false);
              setEditingEntryId(null);
              setDescriptionValue('');
              setDescriptionError(null);
            }
          }}>
            <div className="description-modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="description-modal-header">
                <h2>Add Description</h2>
                <button className="description-modal-close" onClick={() => {
                  setDescriptionPromptOpen(false);
                  setEditingEntryId(null);
                  setDescriptionValue('');
                  setDescriptionError(null);
                }}>
                  ×
                </button>
              </div>
              <div className="description-modal-body">
                <p className="description-modal-instructions">
                  Enter a description for this entry. This will help clarify the record for future reference.
                </p>
                <div className="description-modal-form">
                  <label htmlFor="description-input">
                    Description:
                  </label>
                  <textarea
                    id="description-input"
                    value={descriptionValue}
                    onChange={(e) => setDescriptionValue(e.target.value)}
                    placeholder="Enter description here..."
                    className="description-input"
                    rows="4"
                  />
                  {descriptionError && (
                    <p className="description-modal-error">{descriptionError}</p>
                  )}
                </div>
              </div>
              <div className="description-modal-footer">
                <button
                  className="description-modal-button"
                  onClick={async () => {
                    setDescriptionSaving(true);
                    setDescriptionError(null);
                    try {
                      await updateEntry(editingEntryId, { description: descriptionValue });
                      setDescriptionPromptOpen(false);
                      setEditingEntryId(null);
                      setDescriptionValue('');
                      // Refresh the relevant data
                      if (activeView === 'tickets') {
                        const refreshedTickets = await getTickets();
                        setTickets(refreshedTickets);
                      } else {
                        const refreshedDockets = await getDockets();
                        setDockets(refreshedDockets);
                      }
                    } catch (err) {
                      setDescriptionError(`Failed to save description: ${err.message}`);
                    } finally {
                      setDescriptionSaving(false);
                    }
                  }}
                  disabled={descriptionSaving}
                >
                  {descriptionSaving ? 'Saving...' : 'Save Description'}
                </button>
                <button
                  className="description-modal-button description-modal-button-secondary"
                  onClick={() => {
                    setDescriptionPromptOpen(false);
                    setEditingEntryId(null);
                    setDescriptionValue('');
                    setDescriptionError(null);
                  }}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
      <footer className="app-footer">
        <span>TIL System</span>
        <span>Restaurant operations workspace</span>
      </footer>
    </div>
  );
}

export default App;