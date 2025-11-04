import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';

const API_BASE = process.env.REACT_APP_API_URL;

// Custom Toast Notification Component
const Toast = ({ message, title, type, onClose }) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      onClose();
    }, 5000);
    return () => clearTimeout(timer);
  }, [onClose]);

  const bgColor = type === 'success' ? 'bg-green-600' : 'bg-red-600';
  const icon = type === 'success'
    ? <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
      </svg>
    : <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
      </svg>;

  return (
    <div style={{
      position: 'fixed',
      top: '20px',
      right: '20px',
      zIndex: 9999,
      minWidth: '320px',
      maxWidth: '400px',
      backgroundColor: '#1f2937',
      border: '1px solid #374151',
      borderRadius: '8px',
      boxShadow: '0 10px 25px rgba(0, 0, 0, 0.3)',
      overflow: 'hidden',
      animation: 'slideIn 0.3s ease-out'
    }}>
      <div className={`${bgColor} px-4 py-3 flex items-center justify-between`}>
        <div className="flex items-center gap-3 text-white">
          {icon}
          <span className="font-semibold text-sm">{title}</span>
        </div>
        <button
          onClick={onClose}
          className="text-white hover:bg-white/20 rounded p-1 transition-colors"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      <div className="px-4 py-3 text-gray-200 text-sm leading-relaxed">
        {message}
      </div>
    </div>
  );
};

function DocumentManagementTab() {
  // Upload states
  const [files, setFiles] = useState([]);
  const [prefix, setPrefix] = useState('sop/');
  const [uploadLoading, setUploadLoading] = useState(false);

  // List states
  const [documents, setDocuments] = useState([]);
  const [listPrefix, setListPrefix] = useState('sop/');
  const [listLoading, setListLoading] = useState(false);

  // Delete states - modified to handle individual deletes
  const [deleteLoading, setDeleteLoading] = useState({});

  // Toast state
  const [toast, setToast] = useState(null);




  // Upload functions
  const handleFileChange = (e) => {
    setFiles(Array.from(e.target.files));
  };

  const handleUpload = async () => {
    if (files.length === 0) {
      setToast({
        type: 'error',
        title: 'Error',
        message: 'Please select files to upload'
      });
      return;
    }

    setUploadLoading(true);
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });
    formData.append('prefix', prefix);

    try {
      const response = await axios.post(`${API_BASE}/documents/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      // Show success notification
      const uploadResults = response.data.upload_results || response.data;
      const successCount = uploadResults.successful_uploads || 0;
      const failedCount = uploadResults.failed_uploads || 0;
      const totalFiles = uploadResults.total_files || files.length;

      if (failedCount === 0) {
        setToast({
          type: 'success',
          title: 'Success',
          message: `Data berhasil diupload`
        });
      } else if (successCount === 0) {
        setToast({
          type: 'error',
          title: 'Error',
          message: `Semua file gagal diupload (${failedCount} file)`
        });
      } else {
        setToast({
          type: 'success',
          title: 'Success',
          message: `${successCount} file berhasil diupload, ${failedCount} file gagal`
        });
      }

      // Clear file selection
      setFiles([]);
      // Reset file input
      const fileInput = document.querySelector('input[type="file"]');
      if (fileInput) fileInput.value = '';

      // Auto refresh document list after upload
      handleListDocuments();
    } catch (error) {
      // Show error notification
      const errorMessage = error.response?.data?.detail || error.message;
      setToast({
        type: 'error',
        title: 'Error',
        message: `Upload gagal: ${errorMessage}`
      });
    } finally {
      setUploadLoading(false);
    }
  };

  // List functions
  const handleListDocuments = async () => {
    setListLoading(true);
    try {
      const response = await axios.get(`${API_BASE}/documents`, {
        params: { prefix: listPrefix }
      });
      setDocuments(response.data.documents || []);
    } catch (error) {
      console.error('Error listing documents:', error);
      setDocuments([]);
    } finally {
      setListLoading(false);
    }
  };

  // Modified delete function for individual documents
  const handleDeleteDocument = async (blobName, index) => {
    setDeleteLoading(prev => ({ ...prev, [index]: true }));

    try {
      const response = await axios.delete(`${API_BASE}/documents`, {
        data: { blob_names: [blobName] }
      });

      // Show success toast
      setToast({
        type: 'success',
        title: 'Success',
        message: 'Data berhasil dihapus'
      });

      // Remove the document from the list
      setDocuments(prev => prev.filter((_, i) => i !== index));

    } catch (error) {
      // Show error toast
      const errorMessage = error.response?.data?.detail || error.message;
      setToast({
        type: 'error',
        title: 'Error',
        message: `Gagal menghapus document: ${errorMessage}`
      });
    } finally {
      setDeleteLoading(prev => {
        const newLoading = { ...prev };
        delete newLoading[index];
        return newLoading;
      });
    }
  };


  // Load documents on component mount
  useEffect(() => {
    handleListDocuments();
  }, []);

  const formatFileSize = (bytes) => {
    if (!bytes) return 'Unknown';
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown';
    return new Date(dateString).toLocaleString();
  };

  return (
    <>
      {toast && (
        <Toast
          type={toast.type}
          title={toast.title}
          message={toast.message}
          onClose={() => setToast(null)}
        />
      )}

      <div className="p-6 space-y-6">
        <Card className="glass-effect modern-shadow">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              Document Management
            </CardTitle>
          </CardHeader>

          <CardContent className="space-y-4">
                  {/* Upload Section */}
                  <div className="space-y-3">
                    <label className="text-sm font-medium text-foreground">Upload Files:</label>
                    <div className="relative">
                      <input
                        type="file"
                        multiple
                        onChange={handleFileChange}
                        accept=".pdf,.docx,.doc,.txt,.pptx,.xlsx,.jpg,.jpeg,.png"
                        className="flex h-12 w-full rounded-md border-2 border-dashed border-border bg-card hover:bg-accent px-4 py-3 text-sm text-foreground transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 cursor-pointer"
                      />
                      {files.length === 0 && (
                        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                          <span className="text-muted-foreground text-sm">Click to choose files or drag and drop</span>
                        </div>
                      )}
                    </div>
                    {files.length > 0 && (
                      <div className="text-sm text-muted-foreground">
                        Selected: {files.length} file{files.length > 1 ? 's' : ''}
                      </div>
                    )}
                  </div>

                  <div className="text-center">
                    <Button 
                      onClick={handleUpload} 
                      disabled={uploadLoading}
                      className="px-16"
                    >
                      {uploadLoading ? ' Processing...' : ' Upload Files'}
                    </Button>
                  </div>

                  {/* Document List Section */}
                  <div className="border-t pt-4">
                    <h4 className="text-sm font-medium mb-2">Document List</h4>
                    
                    {listLoading && (
                      <div className="text-center py-4 text-sm text-muted-foreground">
                        Loading documents...
                      </div>
                    )}

                    {documents.length > 0 && (
                      <div className="bg-muted border border-border p-3 rounded-md max-h-64 overflow-auto">
                        <div className="text-sm font-medium mb-3 text-foreground">Documents ({documents.length})</div>
                        <div className="space-y-2">
                          {documents.map((doc, index) => (
                            <div key={index} className="bg-card border border-border p-3 rounded-md text-sm hover:bg-accent transition-colors">
                              <div className="flex items-center justify-between">
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center justify-between mb-1">
                                    <span className="font-medium truncate text-foreground">{doc.display_name || doc.name}</span>
                                    <span className="text-muted-foreground ml-2 text-xs">{formatFileSize(doc.size)}</span>
                                  </div>
                                  <div className="text-muted-foreground text-xs">{formatDate(doc.last_modified)}</div>
                                </div>
                                <Button
                                  onClick={() => handleDeleteDocument(doc.name, index)}
                                  disabled={deleteLoading[index]}
                                  variant="destructive"
                                  size="sm"
                                  className="ml-3 px-3 py-1 text-xs"
                                  title={`Delete ${doc.display_name || doc.name}`}
                                >
                                  {deleteLoading[index] ? 'Deleting...' : 'Delete'}
                                </Button>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {documents.length === 0 && !listLoading && (
                      <div className="bg-muted p-4 rounded-md text-center text-sm text-muted-foreground">
                        No documents found
                      </div>
                    )}
                  </div>
        </CardContent>
      </Card>
    </div>

    <style jsx>{`
      @keyframes slideIn {
        from {
          transform: translateX(100%);
          opacity: 0;
        }
        to {
          transform: translateX(0);
          opacity: 1;
        }
      }
    `}</style>
    </>
  );
}

export default DocumentManagementTab;