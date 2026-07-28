import React, { useState } from 'react';
import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XCircleIcon,
  ArrowPathIcon,
  ShieldCheckIcon,
  DocumentMagnifyingGlassIcon
} from '@heroicons/react/24/outline';

/**
 * BackupVerification Component
 *
 * Verify backup integrity with checksum validation and test restore.
 */
export default function BackupVerification({ backups, onVerify }) {
  const [verifyingId, setVerifyingId] = useState(null);
  const [verificationResults, setVerificationResults] = useState({});

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'verified':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'corrupted':
        return <XCircleIcon className="h-5 w-5 text-red-500" />;
      case 'warning':
        return <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500" />;
      case 'verifying':
        return <ArrowPathIcon className="h-5 w-5 text-blue-500 animate-spin" />;
      default:
        return <DocumentMagnifyingGlassIcon className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'verified':
        return 'text-green-600 dark:text-green-400';
      case 'corrupted':
        return 'text-red-600 dark:text-red-400';
      case 'warning':
        return 'text-yellow-600 dark:text-yellow-400';
      case 'verifying':
        return 'text-blue-600 dark:text-blue-400';
      default:
        return 'text-gray-600 dark:text-gray-400';
    }
  };

  const handleVerify = async (backupId) => {
    setVerifyingId(backupId);
    setVerificationResults({
      ...verificationResults,
      [backupId]: { status: 'verifying', message: 'Verifying backup...' }
    });

    try {
      const result = await onVerify(backupId);
      setVerificationResults({
        ...verificationResults,
        [backupId]: result
      });
    } catch (error) {
      setVerificationResults({
        ...verificationResults,
        [backupId]: {
          status: 'error',
          message: error.message || 'Verification failed'
        }
      });
    } finally {
      setVerifyingId(null);
    }
  };

  const handleVerifyAll = async () => {
    for (const backup of backups) {
      await handleVerify(backup.id);
      // Add delay between verifications
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <ShieldCheckIcon className="h-8 w-8 text-blue-500" />
          <div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Backup Verification
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Verify backup integrity with checksum validation
            </p>
          </div>
        </div>
        <button
          onClick={handleVerifyAll}
          disabled={verifyingId !== null}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
        >
          <ShieldCheckIcon className="h-5 w-5" />
          Verify All Backups
        </button>
      </div>

      {/* Info Box */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <DocumentMagnifyingGlassIcon className="h-5 w-5 text-blue-600 dark:text-blue-500 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-blue-700 dark:text-blue-400">
            <strong>Verification Process:</strong>
            <ul className="list-disc list-inside mt-1 space-y-1">
              <li>Validates file checksums (MD5/SHA256)</li>
              <li>Checks archive integrity</li>
              <li>Verifies all files are accessible</li>
              <li>Tests partial restore (optional)</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Backup List */}
      <div className="space-y-3">
        {backups.map((backup) => {
          const verification = verificationResults[backup.id];
          const isVerifying = verifyingId === backup.id;

          return (
            <div
              key={backup.id}
              className="bg-white dark:bg-gray-800 border dark:border-gray-700 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  {/* Backup Info */}
                  <div className="flex items-center gap-3 mb-3">
                    {verification ? (
                      getStatusIcon(verification.status)
                    ) : (
                      <DocumentMagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
                    )}
                    <div>
                      <h3 className="font-medium text-gray-900 dark:text-white">
                        {backup.id}
                      </h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {formatDate(backup.timestamp)}
                      </p>
                    </div>
                  </div>

                  {/* Backup Details */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm mb-3">
                    <div>
                      <span className="text-gray-600 dark:text-gray-400">Size:</span>
                      <span className="ml-2 font-medium text-gray-900 dark:text-white">
                        {formatBytes(backup.size)}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-600 dark:text-gray-400">Type:</span>
                      <span className="ml-2 font-medium text-gray-900 dark:text-white">
                        {backup.type}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-600 dark:text-gray-400">Files:</span>
                      <span className="ml-2 font-medium text-gray-900 dark:text-white">
                        {backup.files_count?.toLocaleString() || 'N/A'}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-600 dark:text-gray-400">Status:</span>
                      <span className={`ml-2 font-medium capitalize ${getStatusColor(verification?.status || 'unknown')}`}>
                        {verification?.status || 'Not verified'}
                      </span>
                    </div>
                  </div>

                  {/* Verification Result */}
                  {verification && verification.status !== 'verifying' && (
                    <div className={`mt-3 p-3 rounded-lg ${
                      verification.status === 'verified'
                        ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800'
                        : verification.status === 'corrupted'
                        ? 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800'
                        : 'bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800'
                    }`}>
                      <div className="flex items-start gap-2">
                        {getStatusIcon(verification.status)}
                        <div className="flex-1">
                          <div className={`text-sm font-medium ${
                            verification.status === 'verified'
                              ? 'text-green-800 dark:text-green-400'
                              : verification.status === 'corrupted'
                              ? 'text-red-800 dark:text-red-400'
                              : 'text-yellow-800 dark:text-yellow-400'
                          }`}>
                            {verification.message}
                          </div>
                          {verification.details && (
                            <ul className={`text-xs mt-2 space-y-1 ${
                              verification.status === 'verified'
                                ? 'text-green-700 dark:text-green-500'
                                : verification.status === 'corrupted'
                                ? 'text-red-700 dark:text-red-500'
                                : 'text-yellow-700 dark:text-yellow-500'
                            }`}>
                              {verification.details.map((detail, index) => (
                                <li key={index} className="flex items-start gap-1">
                                  <span>•</span>
                                  <span>{detail}</span>
                                </li>
                              ))}
                            </ul>
                          )}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Verifying State */}
                  {isVerifying && (
                    <div className="mt-3 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                      <div className="flex items-center gap-2">
                        <ArrowPathIcon className="h-4 w-4 text-blue-600 dark:text-blue-400 animate-spin" />
                        <span className="text-sm text-blue-700 dark:text-blue-400">
                          Verifying backup integrity...
                        </span>
                      </div>
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="ml-4">
                  <button
                    onClick={() => handleVerify(backup.id)}
                    disabled={isVerifying}
                    className="px-3 py-2 bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-50 flex items-center gap-2 text-sm"
                  >
                    {isVerifying ? (
                      <>
                        <ArrowPathIcon className="h-4 w-4 animate-spin" />
                        Verifying...
                      </>
                    ) : (
                      <>
                        <ShieldCheckIcon className="h-4 w-4" />
                        Verify
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* Fix Corrupted Button (if needed) */}
              {verification?.status === 'corrupted' && (
                <div className="mt-3 pt-3 border-t dark:border-gray-700">
                  <button className="px-3 py-1 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm flex items-center gap-2">
                    <ExclamationTriangleIcon className="h-4 w-4" />
                    Attempt Recovery
                  </button>
                </div>
              )}
            </div>
          );
        })}

        {backups.length === 0 && (
          <div className="text-center py-12 text-gray-500 dark:text-gray-400">
            <DocumentMagnifyingGlassIcon className="h-16 w-16 mx-auto mb-4 opacity-50" />
            <p>No backups available to verify</p>
          </div>
        )}
      </div>

      {/* Summary */}
      {Object.keys(verificationResults).length > 0 && (
        <div className="bg-white dark:bg-gray-800 border dark:border-gray-700 rounded-lg p-4">
          <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-3">
            Verification Summary
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-600 dark:text-gray-400">Total:</span>
              <span className="ml-2 font-medium text-gray-900 dark:text-white">
                {Object.keys(verificationResults).length}
              </span>
            </div>
            <div>
              <span className="text-gray-600 dark:text-gray-400">Verified:</span>
              <span className="ml-2 font-medium text-green-600 dark:text-green-400">
                {Object.values(verificationResults).filter(r => r.status === 'verified').length}
              </span>
            </div>
            <div>
              <span className="text-gray-600 dark:text-gray-400">Warnings:</span>
              <span className="ml-2 font-medium text-yellow-600 dark:text-yellow-400">
                {Object.values(verificationResults).filter(r => r.status === 'warning').length}
              </span>
            </div>
            <div>
              <span className="text-gray-600 dark:text-gray-400">Corrupted:</span>
              <span className="ml-2 font-medium text-red-600 dark:text-red-400">
                {Object.values(verificationResults).filter(r => r.status === 'corrupted').length}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
