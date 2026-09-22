import { useState, useEffect } from 'react';
import './App.css';
import { uploadTicketScreenshotBatch, uploadDocketImageBatch } from './api/upload';
import { exportVoidReconciliation, getVoidReconciliation } from './api/voids';
import { exportDockets, exportTickets, getDockets, getTickets } from './api/records';

// Fallback options shown only while the table is empty; real options are
// derived from the restaurant values the backend actually returns.
function App() {
  const [ticketUploadLoading, setTicketUploadLoading] = useState(false);
  const [ticketUploadError, setTicketUploadError] = useState(null);
  const [ticketUploadItems, setTicketUploadItems] = useState([]);
  const [showTicketData, setShowTicketData] = useState(false);
  const [docketUploadLoading, setDocketUploadLoading] = useState(false);
  const [docketUploadError, setDocketUploadError] = useState(null);
  const [docketUploadItems, setDocketUploadItems] = useState([]);
  const [showDocketData, setShowDocketData] = useState(false);
  const [activeView, setActiveView] = useState('tickets');
  const [tickets, setTickets] = useState([]);
  const [dockets, setDockets] = useState([]);
  const [recordsLoading, setRecordsLoading] = useState(false);
  const [recordsError, setRecordsError] = useState(null);
  const [voidReconciliation, setVoidReconciliation] = useState(null);
  const [voidLoading, setVoidLoading] = useState(false);
  const [voidError, setVoidError] = useState(null);
  useEffect(() => {
    if (activeView !== 'voids') return;
    let cancelled = false;
    setVoidLoading(true);
    setVoidError(null);
    getVoidReconciliation()
      .then((data) => {
        if (!cancelled) setVoidReconciliation(data);
      })
      .catch((err) => {
        if (!cancelled) setVoidError(err.message);
      })
      .finally(() => {
        if (!cancelled) setVoidLoading(false);
      });
    return () => { cancelled = true; };
  }, [activeView]);

  useEffect(() => {
    if (activeView !== 'tickets' && activeView !== 'dockets') return;
    let cancelled = false;
    setRecordsLoading(true);
    setRecordsError(null);
    const request = activeView === 'tickets' ? getTickets() : getDockets();
    request
      .then((data) => {
        if (cancelled) return;
        if (activeView === 'tickets') setTickets(data);
        else setDockets(data);
      })
      .catch((err) => {
        if (!cancelled) setRecordsError(err.message);
      })
      .finally(() => {
        if (!cancelled) setRecordsLoading(false);
      });
    return () => { cancelled = true; };
  }, [activeView]);

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
      setShowTicketData(false);
      setActiveView('tickets');
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
      setShowDocketData(false);
      setActiveView('dockets');
    } catch (err) {
      setDocketUploadItems(prev => prev.map(item => ({ ...item, status: 'error', message: err.message })));
      setDocketUploadError(err.message);
    } finally {
      setDocketUploadLoading(false);
    }
  };

  const handleVoidExport = async () => {
    try {
      await exportVoidReconciliation();
    } catch (err) {
      alert(`Error exporting void reconciliation: ${err.message}`);
    }
  };

  const handleRecordsExport = async () => {
    try {
      if (activeView === 'tickets') await exportTickets();
      if (activeView === 'dockets') await exportDockets();
    } catch (err) {
      alert(`Error exporting parsed data: ${err.message}`);
    }
  };

  const recordRows = activeView === 'tickets' ? tickets : dockets;

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
          <div className="view-tabs" role="tablist" aria-label="Record views">
            {[
              ['tickets', 'Tickets'],
              ['dockets', 'Dockets'],
              ['voids', 'Voids tally'],
            ].map(([view, label]) => (
              <button
                key={view}
                className={`view-toggle ${activeView === view ? 'active' : ''}`}
                onClick={() => setActiveView(view)}
                role="tab"
                aria-selected={activeView === view}
              >
                {label}
              </button>
            ))}
          </div>
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

        {activeView === 'voids' ? (
          <section className="voids-section">
            <div className="section-heading voids-heading">
              <div>
                <p className="eyebrow">Division 5c</p>
                <h2>Void reconciliation</h2>
                <p className="voids-intro">Voided ticket items stay aligned with their docket evidence. Matched rows rise to the top; gaps remain visible.</p>
              </div>
              <button className="export-button" onClick={handleVoidExport} disabled={voidLoading || !voidReconciliation?.rows?.length}>
                <span>↓</span> Export voids
              </button>
            </div>
            {voidLoading && <p className="loading-state">Building void alignment...</p>}
            {voidError && <p className="error-state">Error: {voidError}</p>}
            {voidReconciliation && (
              <>
                <div className="void-summary" aria-live="polite">
                  <span><strong>{voidReconciliation.summary.void_items}</strong> void items</span>
                  <span className="summary-matched"><strong>{voidReconciliation.summary.matched}</strong> matched</span>
                  <span className="summary-review"><strong>{voidReconciliation.summary.needs_review}</strong> review</span>
                  <span className="summary-unmatched"><strong>{voidReconciliation.summary.unmatched}</strong> unmatched</span>
                </div>
                <div className="void-table-wrap">
                  {voidReconciliation.rows.length === 0 ? (
                    <p className="empty-table">No voided ticket items are available.</p>
                  ) : (
                    <div className="void-grid" role="table" aria-label="Voided ticket and docket alignment">
                      <div className="void-grid-header" role="row">
                        <span>Voided ticket item</span>
                        <span>Docket evidence</span>
                      </div>
                      {voidReconciliation.rows.map((row) => {
                        const item = row.ticket.item || {};
                        const docket = row.docket;
                        return (
                          <div className={`void-grid-row void-${row.status}`} role="row" key={`${row.row_position}-${row.ticket.ticket_id}-${item.name}`}>
                            <div className="void-ticket-cell">
                              <div className="void-cell-topline">
                                <span className="void-position">{String(row.row_position).padStart(2, '0')}</span>
                                <strong>{row.ticket.ticket_id}</strong>
                                <span className="status-badge review">VOID</span>
                              </div>
                              <p>{item.name || 'Unnamed item'}</p>
                              <span className="void-item-meta">Qty {item.quantity || '—'} · Unit {item.unit_price || '—'} · Total {item.total || '—'}</span>
                            </div>
                            <div className="void-docket-cell">
                              {docket ? (
                                <>
                                  <div className="void-cell-topline">
                                    <span className={`status-badge ${row.status === 'matched' ? 'matched' : 'review'}`}>{row.status}</span>
                                    <span className="docket-order">Order {docket.docket_order_no}</span>
                                  </div>
                                  <p>{docket.item || 'Docket item not parsed'}</p>
                                  <span className="void-item-meta">{docket.handwritten_reason || 'No handwritten reason captured'}</span>
                                </>
                              ) : row.status === 'needs_review' ? (
                                <>
                                  <div className="void-cell-topline"><span className="status-badge review">Needs review</span></div>
                                  <p>Ambiguous docket match</p>
                                  <span className="void-item-meta">{row.docket_candidates.length} candidates share order {row.trailing_order_no}</span>
                                </>
                              ) : (
                                <>
                                  <div className="void-cell-topline"><span className="status-badge unmatched">No docket found</span></div>
                                  <p>Explanation missing</p>
                                  <span className="void-item-meta">No docket for trailing order {row.trailing_order_no}</span>
                                </>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </>
            )}
          </section>
        ) : (
        <>

        <section className="bulk-upload-grid">
          <div className="upload-section bulk-panel">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Ticket screenshots</p>
                <h2>Upload screenshots in bulk</h2>
              </div>
              <span className="section-icon">IMG</span>
            </div>
            <label className="upload-dropzone" htmlFor="ticket-screenshot-upload">
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
                if (files.length > 0) {
                  handleTicketScreenshotUpload(files);
                  e.target.value = '';
                }
              }}
              disabled={ticketUploadLoading}
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
          </div>

          <div className="upload-section bulk-panel">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Bulk docket</p>
                <h2>Discrepancy images</h2>
              </div>
              <span className="section-icon">IMG</span>
            </div>
            <label className="upload-dropzone" htmlFor="docket-upload">
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
                if (files.length > 0) {
                  handleDocketUpload(files);
                  e.target.value = '';
                }
              }}
              disabled={docketUploadLoading}
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
                setActiveView('dockets');
                setShowDocketData((visible) => !visible);
              }}>
                {showDocketData ? 'Hide data' : 'Show data'}
              </button>
            )}
          </div>
        </section>
        {(activeView === 'tickets' ? showTicketData : showDocketData) && <section className="parsed-record-section">
          <div className="section-heading table-heading">
            <div>
              <p className="eyebrow">Parsed data</p>
              <h2>{activeView === 'tickets' ? 'Ticket information' : 'Docket information'} <span className="entry-count">{recordRows.length}</span></h2>
            </div>
            <button className="export-button" onClick={handleRecordsExport} disabled={recordsLoading || recordRows.length === 0}>
              <span>↓</span> Export {activeView === 'tickets' ? 'tickets' : 'dockets'} CSV
            </button>
          </div>
          {recordsLoading && <p className="loading-state">Loading parsed {activeView}...</p>}
          {recordsError && <p className="error-state">Error: {recordsError}</p>}
          <div className="table-scroll">
            {activeView === 'tickets' ? (
              <table className="entries-table parsed-table">
                <thead><tr>
                  <th className="ticket-id-header">Ticket Number</th><th>Uploaded</th><th>Restaurant</th><th>Date</th><th>Terminal</th>
                  <th>Table</th><th>Department</th><th>User</th><th>Payment Status</th>
                  <th>Credit Card Amount</th><th>Items</th><th>Ticket Total</th>
                  <th>Grand Total</th><th>Charged</th>
                </tr></thead>
                <tbody>
                  {tickets.length === 0 ? <tr><td colSpan="14" className="empty-table">No parsed ticket screenshots yet.</td></tr> : tickets.map((ticket) => (
                    <tr key={ticket.ticket_id}>
                      <td className="ticket-id-cell"><strong>{ticket.ticket_id || 'Missing ticket ID'}</strong></td>
                      <td>{ticket.uploaded_at ? new Date(`${ticket.uploaded_at}Z`).toLocaleString() : '—'}</td>
                      <td>{ticket.restaurant || '—'}</td><td>{ticket.date || '—'}</td>
                      <td>{ticket.terminal || '—'}</td><td>{ticket.table || '—'}</td>
                      <td>{ticket.department || '—'}</td><td>{ticket.user || '—'}</td>
                      <td>{ticket.payment_status || '—'}</td><td>{ticket.credit_card_amount || '—'}</td>
                      <td>
                        {ticket.items?.length ? (
                          <details>
                            <summary>{ticket.items.length} item{ticket.items.length === 1 ? '' : 's'}</summary>
                            <table className="nested-items-table">
                              <thead><tr><th>Item</th><th>Category</th><th>Price</th><th>Qty</th><th>Total</th></tr></thead>
                              <tbody>{ticket.items.map((item, index) => (
                                <tr key={`${ticket.ticket_id}-${index}`} className={item.is_void ? 'parsed-void-row' : ''}>
                                  <td>{item.item || '—'}{item.is_void ? ' (void)' : ''}</td>
                                  <td>{item.category || '—'}</td><td>{item.price || '—'}</td>
                                  <td>{item.qty || '—'}</td><td>{item.total || '—'}</td>
                                </tr>
                              ))}</tbody>
                            </table>
                          </details>
                        ) : '—'}
                      </td>
                      <td>{ticket.ticket_total || '—'}</td><td>{ticket.grand_total || '—'}</td>
                      <td>{ticket.charged || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <table className="entries-table parsed-table">
                <thead><tr>
                  <th>Order No</th><th>Date</th><th>Time</th><th>Item</th>
                  <th>Discrepancy Type</th><th>Handwritten Reason</th>
                </tr></thead>
                <tbody>
                  {dockets.length === 0 ? <tr><td colSpan="6" className="empty-table">No parsed dockets yet.</td></tr> : dockets.map((docket) => (
                    <tr key={docket.id} className={docket.review_required ? 'parsed-review-row' : ''}>
                      <td><strong>{docket.order_number || '—'}</strong></td>
                      <td>{docket.date || '—'}</td><td>{docket.time || '—'}</td>
                      <td>{docket.item || '—'}</td>
                      <td><span className={`badge badge-${docket.discrepancy_type || 'unknown'}`}>{docket.discrepancy_type || 'unknown'}</span></td>
                      <td className="handwritten-cell">{docket.description || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </section>}
        </>
        )}
      </main>
    </div>
  );
}

export default App;