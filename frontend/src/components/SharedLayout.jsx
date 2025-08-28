import React, { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import './SharedLayout.css';

function SharedLayout({ children, activeTab }) {
  const [entries, setEntries] = useState([]);
  const [selectedEntry, setSelectedEntry] = useState(null);
  const [isPanelCollapsed, setIsPanelCollapsed] = useState(true);
  const [newEntryId, setNewEntryId] = useState(null);
  const [sidebarWidth, setSidebarWidth] = useState(500); // Default width
  const prevEntriesRef = useRef([]);
  const entriesListRef = useRef(null);
  const entryDetailRef = useRef(null);
  const entriesContainerRef = useRef(null);
  const isResizingRef = useRef(false);
  const isHorizontalResizingRef = useRef(false);
  const startYRef = useRef(0);
  const startXRef = useRef(0);
  const startHeightsRef = useRef({ list: 0, detail: 0 });
  const startWidthRef = useRef(0);

  // Use useCallback to create a stable function reference
  const fetchEntries = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      console.log("Using token for entries:", token); // Debug log
      
      const response = await axios.get('/api/entries', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      const newEntries = response.data;
      console.log("Entries received:", newEntries); // Debug log
      
      // Check if there's a new entry by comparing with previous entries
      if (prevEntriesRef.current.length > 0 && newEntries.length > prevEntriesRef.current.length) {
        // Find the new entry (the one that wasn't in the previous list)
        const newEntry = newEntries.find(entry => 
          !prevEntriesRef.current.some(prevEntry => prevEntry.entry_id === entry.entry_id)
        );
        
        if (newEntry) {
          setNewEntryId(newEntry.entry_id);
          // Clear the new entry ID after animation duration
          setTimeout(() => {
            setNewEntryId(null);
          }, 1000); // Slightly longer than animation to ensure it completes
        }
      }
      
      setEntries(newEntries);
      prevEntriesRef.current = newEntries;
    } catch (error) {
      console.error('Error fetching entries:', error.response?.data || error.message);
    }
  }, []);

  useEffect(() => {
    fetchEntries();
    
    // Expose the refresh function globally so it can be called from other components
    window.refreshEntries = () => {
      // Add a slight delay before refreshing to make the animation more noticeable
      setTimeout(fetchEntries, 300);
    };
    
    // Clean up the global function when component unmounts
    return () => {
      window.refreshEntries = null;
    };
  }, [fetchEntries]);

  // Update CSS variable when sidebar width changes
  useEffect(() => {
    document.documentElement.style.setProperty('--sidebar-width', `${sidebarWidth}px`);
    console.log("Set sidebar width to:", sidebarWidth); // Debug log
  }, [sidebarWidth]);

  // Handle vertical resize functionality
  const handleResizeStart = (e) => {
    isResizingRef.current = true;
    startYRef.current = e.clientY;
    
    if (entriesListRef.current && entryDetailRef.current) {
      startHeightsRef.current = {
        list: entriesListRef.current.getBoundingClientRect().height,
        detail: entryDetailRef.current.getBoundingClientRect().height
      };
    }
    
    // Add event listeners for mouse move and mouse up
    document.addEventListener('mousemove', handleResizeMove);
    document.addEventListener('mouseup', handleResizeEnd);
  };

  const handleResizeMove = (e) => {
    if (!isResizingRef.current) return;
    
    const deltaY = e.clientY - startYRef.current;
    
    if (entriesListRef.current && entryDetailRef.current) {
      const containerHeight = entriesListRef.current.parentElement.getBoundingClientRect().height;
      const newListHeight = Math.max(100, Math.min(containerHeight - 100, startHeightsRef.current.list + deltaY));
      const newDetailHeight = containerHeight - newListHeight - 10; // 10px for the resize handle
      
      entriesListRef.current.style.flex = 'none';
      entriesListRef.current.style.height = `${newListHeight}px`;
      
      entryDetailRef.current.style.flex = 'none';
      entryDetailRef.current.style.height = `${newDetailHeight}px`;
    }
  };

  const handleResizeEnd = () => {
    isResizingRef.current = false;
    isHorizontalResizingRef.current = false;
    document.removeEventListener('mousemove', handleResizeMove);
    document.removeEventListener('mousemove', handleHorizontalResizeMove);
    document.removeEventListener('mouseup', handleResizeEnd);
    
    // Remove the resizing class from the handle
    const handle = document.querySelector('.horizontal-resize-handle');
    if (handle) {
      handle.classList.remove('resizing');
    }
  };

  // Handle horizontal resize functionality
  const handleHorizontalResizeStart = (e) => {
    e.preventDefault();
    isHorizontalResizingRef.current = true;
    startXRef.current = e.clientX;
    
    if (entriesContainerRef.current) {
      startWidthRef.current = entriesContainerRef.current.getBoundingClientRect().width;
    }
    
    // Add the resizing class to the handle
    e.currentTarget.classList.add('resizing');
    
    // Add event listeners for mouse move and mouse up
    document.addEventListener('mousemove', handleHorizontalResizeMove);
    document.addEventListener('mouseup', handleResizeEnd);
  };

  const handleHorizontalResizeMove = (e) => {
    if (!isHorizontalResizingRef.current) return;
    
    const deltaX = startXRef.current - e.clientX; // Reversed because we're resizing from right to left
    
    if (entriesContainerRef.current) {
      const newWidth = Math.max(250, Math.min(800, startWidthRef.current + deltaX));
      entriesContainerRef.current.style.width = `${newWidth}px`;
      setSidebarWidth(newWidth);
    }
  };

  const handleEntryClick = (entry) => {
    setSelectedEntry(entry);
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return date.toLocaleDateString(undefined, options);
  };

  return (
    <div className={`layout-container ${isPanelCollapsed ? 'panel-collapsed' : ''}`}>
      <div className="content-area">
        {React.cloneElement(children, { 
          journalToggleButton: (
            <button 
              type="button"
              className="entries-toggle-button"
              onClick={() => setIsPanelCollapsed(!isPanelCollapsed)}
            >
              {isPanelCollapsed ? 'Show Journal' : 'Hide Journal'}
            </button>
          )
        })}
      </div>
      
      <div 
        className={`entries-container ${isPanelCollapsed ? 'collapsed' : ''}`}
        ref={entriesContainerRef}
        style={{ width: `${sidebarWidth}px` }}
      >
        <div 
          className="horizontal-resize-handle"
          onMouseDown={handleHorizontalResizeStart}
          title="Drag to resize width"
        ></div>
        
        <div className="entries-header">
          <h2>Your Journal</h2>
        </div>
        <div className="entries-list" ref={entriesListRef}>
          {entries.length === 0 ? (
            <div className="empty-entries">
              <p>No entries yet. Start journaling!</p>
            </div>
          ) : (
            entries.map((entry) => (
              <div 
                id={`entry-${entry.entry_id}`}
                key={entry.entry_id} 
                className={`entry-item ${selectedEntry?.entry_id === entry.entry_id ? 'selected' : ''} ${newEntryId === entry.entry_id ? 'new-entry' : ''}`}
                onClick={() => handleEntryClick(entry)}
              >
                <div className="entry-header">
                  <span className="entry-id">#{entry.user_entry_id || entry.entry_id}</span>
                  <span className="entry-date">{formatDate(entry.created_at)}</span>
                </div>
                <div className="entry-preview">
                  {entry.content.length > 100 
                    ? entry.content.substring(0, 100) + '...' 
                    : entry.content}
                </div>
              </div>
            ))
          )}
        </div>
        
        {selectedEntry && (
          <>
            <div 
              className="resize-handle" 
              onMouseDown={handleResizeStart}
              title="Drag to resize height"
            ></div>
            <div className="entry-detail" ref={entryDetailRef}>
              <h3>Entry #{selectedEntry.user_entry_id || selectedEntry.entry_id}</h3>
              <div className="entry-date-full">{formatDate(selectedEntry.created_at)}</div>
              <div className="entry-content">{selectedEntry.content}</div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default SharedLayout; 