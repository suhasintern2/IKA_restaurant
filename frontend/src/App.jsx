import { useState, useEffect } from 'react';
import './App.css';
import { uploadTicketScreenshotBatch, uploadDocketImageBatch } from './api/upload';
import { exportDockets, exportTickets, getDockets, getTickets } from './api/records';

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
  const activeView = 'tickets';
  const [tickets, setTickets] = useState([]);
  const [dockets, setDockets] = useState([]);
  const [selectedRestaurant, setSelectedRestaurant] = useState('');
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [recordsLoading, setRecordsLoading] = useState(false);
  const [recordsError, setRecordsError] = useState(null);

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

  const handleRecordsExport = async (view) => {
    try {
      if (view === 'tickets') await exportTickets();
      if (view === 'dockets') await exportDockets();
    } catch (err) {
      alert(`Error exporting parsed data: ${err.message}`);
    }
  };

  const recordRows = activeView === 'tickets' ? tickets : dockets;
  const restaurantOptions = [...new Set(tickets.map((ticket) => ticket.restaurant).filter(Boolean))].sort();
  const filteredTickets = selectedRestaurant
    ? tickets.filter((ticket) => ticket.restaurant === selectedRestaurant)
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

  const renderTicketTable = (rows, label) => (
    <div className="upload-data-table">
      <p className="eyebrow">{label}</p>
      <div className="table-scroll">
        <table className="entries-table parsed-table">
          <thead><tr>
            <th className="ticket-id-header">Ticket Number</th><th>Uploaded</th><th>Restaurant</th><th>Date</th><th>Terminal</th>
            <th>Table</th><th>Department</th><th>User</th><th>Payment Status</th><th>Credit Card Amount</th><th>Items</th><th>Ticket Total</th><th>Grand Total</th><th>Charged</th>
          </tr></thead>
          <tbody>
            {rows.length === 0 ? <tr><td colSpan="14" className="empty-table">No parsed ticket screenshots yet.</td></tr> : rows.map((ticket) => (
              <tr key={ticket.ticket_id} className={`ticket-select-row ${selectedTicket?.ticket_id === ticket.ticket_id ? 'selected-ticket-row' : ''}`} onClick={() => setSelectedTicket(ticket)} tabIndex="0" onKeyDown={(event) => { if (event.key === 'Enter') setSelectedTicket(ticket); }}>
                <td className="ticket-id-cell"><strong>{ticket.ticket_id || 'Missing ticket ID'}</strong></td>
                <td>{ticket.uploaded_at ? new Date(`${ticket.uploaded_at}Z`).toLocaleString() : '—'}</td>
                <td>{ticket.restaurant || '—'}</td><td>{ticket.date || '—'}</td><td>{ticket.terminal || '—'}</td><td>{ticket.table || '—'}</td>
                <td>{ticket.department || '—'}</td><td>{ticket.user || '—'}</td><td>{ticket.payment_status || '—'}</td><td>{ticket.credit_card_amount || '—'}</td>
                <td>{ticket.items?.length ? `${ticket.items.length} item${ticket.items.length === 1 ? '' : 's'}` : '—'}</td>
                <td>{ticket.ticket_total || '—'}</td><td>{ticket.grand_total || '—'}</td><td>{ticket.charged || '—'}</td>
              </tr>
            ))}
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
          <thead><tr><th>Order No</th><th>Date</th><th>Time</th><th>Item</th><th>Discrepancy Type</th><th>Handwritten Reason</th></tr></thead>
          <tbody>
            {rows.length === 0 ? <tr><td colSpan="6" className="empty-table">No parsed dockets yet.</td></tr> : rows.map((docket) => (
              <tr key={docket.id} className={docket.review_required ? 'parsed-review-row' : ''}>
                <td><strong>{docket.order_number || '—'}</strong></td><td>{docket.date || '—'}</td><td>{docket.time || '—'}</td><td>{docket.item || '—'}</td>
                <td><span className={`badge badge-${docket.discrepancy_type || 'unknown'}`}>{docket.discrepancy_type || 'unknown'}</span></td><td className="handwritten-cell">{docket.description || '—'}</td>
              </tr>
            ))}
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
            {renderTicketTable(filteredTickets, 'Ticket screenshots data')}
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
              <button className="show-data-button" onClick={() => setSelectedTicket(null)}>Back to tickets</button>
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
      </main>
      <footer className="app-footer">
        <span>TIL System</span>
        <span>Restaurant operations workspace</span>
      </footer>
    </div>
  );
}

export default App;