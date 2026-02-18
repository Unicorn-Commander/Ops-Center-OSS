/**
 * HostedWebsitesGrid - All domains hosted via Traefik
 * Groups related domains (main site + API) hierarchically
 */

import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  GlobeAltIcon,
  LockClosedIcon,
  LockOpenIcon,
  ArrowTopRightOnSquareIcon,
  CheckCircleIcon,
  XCircleIcon,
  QuestionMarkCircleIcon,
  MagnifyingGlassIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  ChevronRightIcon,
  ServerIcon,
  CodeBracketIcon
} from '@heroicons/react/24/outline';

// Extract domain from Traefik rule
const extractDomain = (rule) => {
  if (!rule) return null;
  const match = rule.match(/Host\(`([^`]+)`\)/);
  return match ? match[1] : null;
};

// Get base name from subdomain (e.g., "lavora-api.your-domain.com" -> "lavora")
const getBaseName = (domain) => {
  const parts = domain.split('.');
  if (parts.length < 2) return domain;

  let subdomain = parts[0];
  // Remove common suffixes to get base name
  subdomain = subdomain.replace(/-api$/, '')
                       .replace(/-backend$/, '')
                       .replace(/-admin$/, '')
                       .replace(/-ws$/, '')
                       .replace(/-oauth$/, '')
                       .replace(/-http$/, '');
  return subdomain;
};

// Determine if domain is an API/secondary domain
const isSecondaryDomain = (domain) => {
  const subdomain = domain.split('.')[0];
  return subdomain.includes('-api') ||
         subdomain.includes('-backend') ||
         subdomain.includes('-admin') ||
         subdomain.includes('-ws') ||
         subdomain.includes('-oauth') ||
         subdomain.includes('-http');
};

// Status indicator component
function StatusDot({ status }) {
  const colors = {
    up: 'bg-green-500',
    down: 'bg-red-500',
    unknown: 'bg-gray-500',
  };
  return (
    <span className={`w-2 h-2 rounded-full ${colors[status]} flex-shrink-0`} />
  );
}

// Single domain row component
function DomainRow({ website, isChild = false, onClick }) {
  const statusColors = {
    up: 'text-green-400',
    down: 'text-red-400',
    unknown: 'text-gray-400',
  };

  return (
    <motion.div
      whileHover={{ backgroundColor: 'rgba(255,255,255,0.05)' }}
      className={`flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer group transition-all ${isChild ? 'ml-6 border-l-2 border-gray-700' : ''}`}
      onClick={onClick}
    >
      {/* Icon */}
      {isChild ? (
        <CodeBracketIcon className="h-4 w-4 text-gray-500 flex-shrink-0" />
      ) : (
        <GlobeAltIcon className="h-4 w-4 text-blue-400 flex-shrink-0" />
      )}

      {/* SSL indicator */}
      {website.hasSSL ? (
        <LockClosedIcon className="h-3 w-3 text-green-400 flex-shrink-0" />
      ) : (
        <LockOpenIcon className="h-3 w-3 text-yellow-400 flex-shrink-0" />
      )}

      {/* Domain */}
      <span className={`text-sm flex-1 truncate ${isChild ? 'text-gray-400' : 'text-white font-medium'}`}>
        {website.domain}
      </span>

      {/* Status */}
      <StatusDot status={website.status} />

      {/* Open link */}
      <ArrowTopRightOnSquareIcon className="h-3 w-3 text-gray-500 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0" />
    </motion.div>
  );
}

// Domain group component (main + children)
function DomainGroup({ main, children, websiteStatus, onDomainClick, initialExpanded = false }) {
  const [isExpanded, setIsExpanded] = useState(initialExpanded);

  // Calculate group status (up if main is up, or all children up)
  const allUp = [main, ...children].every(w => w.status === 'up');
  const someDown = [main, ...children].some(w => w.status === 'down');
  const groupStatus = someDown ? 'down' : (allUp ? 'up' : 'unknown');

  return (
    <div className="border border-white/10 rounded-lg overflow-hidden bg-white/5">
      {/* Main domain header */}
      <div
        className="flex items-center gap-2 px-3 py-2 cursor-pointer hover:bg-white/5 transition-colors"
        onClick={() => children.length > 0 && setIsExpanded(!isExpanded)}
      >
        {/* Expand/collapse icon */}
        {children.length > 0 ? (
          <motion.div
            initial={false}
            animate={{ rotate: isExpanded ? 90 : 0 }}
            transition={{ duration: 0.2 }}
          >
            <ChevronRightIcon className="h-4 w-4 text-gray-500" />
          </motion.div>
        ) : (
          <div className="w-4" />
        )}

        {/* Main domain icon */}
        <GlobeAltIcon className="h-4 w-4 text-blue-400 flex-shrink-0" />

        {/* SSL */}
        {main.hasSSL ? (
          <LockClosedIcon className="h-3 w-3 text-green-400 flex-shrink-0" />
        ) : (
          <LockOpenIcon className="h-3 w-3 text-yellow-400 flex-shrink-0" />
        )}

        {/* Domain name */}
        <span
          className="text-sm text-white font-medium flex-1 truncate hover:text-blue-400"
          onClick={(e) => { e.stopPropagation(); onDomainClick(main); }}
        >
          {main.domain}
        </span>

        {/* Child count badge */}
        {children.length > 0 && (
          <span className="text-xs text-gray-500 bg-gray-700/50 px-2 py-0.5 rounded">
            +{children.length} {children.length === 1 ? 'endpoint' : 'endpoints'}
          </span>
        )}

        {/* Status */}
        <StatusDot status={groupStatus} />

        {/* Open link */}
        <ArrowTopRightOnSquareIcon
          className="h-3 w-3 text-gray-500 hover:text-white transition-colors flex-shrink-0"
          onClick={(e) => { e.stopPropagation(); onDomainClick(main); }}
        />
      </div>

      {/* Children (expanded) */}
      <AnimatePresence>
        {isExpanded && children.length > 0 && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="border-t border-white/5 bg-black/20"
          >
            {children.map((child) => (
              <DomainRow
                key={child.domain}
                website={child}
                isChild={true}
                onClick={() => onDomainClick(child)}
              />
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default function HostedWebsitesGrid({
  routes = [],
  websiteStatus = {},
  loading = false,
  error = null,
  glassStyles = {},
  className = ''
}) {
  const [searchQuery, setSearchQuery] = useState('');
  const [showAll, setShowAll] = useState(false);
  const INITIAL_DISPLAY_COUNT = 8;

  // Parse routes and group by base name
  const groupedWebsites = useMemo(() => {
    // Parse routes to extract domains
    const websites = routes
      .map(route => {
        const domain = extractDomain(route.rule);
        if (!domain) return null;
        return {
          domain,
          service: route.service,
          hasSSL: !!route.tls,
          status: websiteStatus[domain] || 'unknown',
          rule: route.rule,
          name: route.name,
          baseName: getBaseName(domain),
          isSecondary: isSecondaryDomain(domain)
        };
      })
      .filter(Boolean);

    // Group by base name
    const groups = {};

    websites.forEach(website => {
      const key = website.baseName;
      if (!groups[key]) {
        groups[key] = { main: null, children: [] };
      }

      if (website.isSecondary) {
        groups[key].children.push(website);
      } else {
        // If we already have a main, move it to children if this one is shorter
        if (groups[key].main) {
          if (website.domain.length < groups[key].main.domain.length) {
            groups[key].children.push(groups[key].main);
            groups[key].main = website;
          } else {
            groups[key].children.push(website);
          }
        } else {
          groups[key].main = website;
        }
      }
    });

    // Convert to array and handle groups without a main
    const result = Object.entries(groups).map(([baseName, group]) => {
      // If no main, promote the first child
      if (!group.main && group.children.length > 0) {
        group.main = group.children.shift();
      }
      return {
        baseName,
        main: group.main,
        children: group.children.sort((a, b) => a.domain.localeCompare(b.domain))
      };
    }).filter(g => g.main); // Remove empty groups

    // Sort by base name
    return result.sort((a, b) => a.baseName.localeCompare(b.baseName));
  }, [routes, websiteStatus]);

  // Filter by search
  const filteredGroups = useMemo(() => {
    if (!searchQuery) return groupedWebsites;

    const query = searchQuery.toLowerCase();
    return groupedWebsites.filter(group => {
      const mainMatches = group.main.domain.toLowerCase().includes(query);
      const childMatches = group.children.some(c => c.domain.toLowerCase().includes(query));
      return mainMatches || childMatches;
    });
  }, [groupedWebsites, searchQuery]);

  // Paginate
  const displayedGroups = showAll
    ? filteredGroups
    : filteredGroups.slice(0, INITIAL_DISPLAY_COUNT);

  const hasMore = filteredGroups.length > INITIAL_DISPLAY_COUNT;

  // Handle domain click
  const handleDomainClick = (website) => {
    const protocol = website.hasSSL ? 'https' : 'http';
    window.open(`${protocol}://${website.domain}`, '_blank');
  };

  // Stats
  const totalDomains = routes.length;
  const totalGroups = groupedWebsites.length;
  const upCount = Object.values(websiteStatus).filter(s => s === 'up').length;
  const downCount = Object.values(websiteStatus).filter(s => s === 'down').length;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`${glassStyles.card || 'backdrop-blur-xl bg-white/10 border border-white/20'} rounded-2xl p-6 shadow-xl ${className}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-xl flex items-center justify-center shadow-lg">
            <GlobeAltIcon className="h-5 w-5 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">Hosted Websites</h3>
            <p className="text-sm text-gray-400">
              {totalGroups} sites • {totalDomains} endpoints •
              <span className="text-green-400 ml-1">{upCount} up</span>
              {downCount > 0 && <span className="text-red-400 ml-1">• {downCount} down</span>}
            </p>
          </div>
        </div>

        {/* Search */}
        <div className="relative">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search domains..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 pr-4 py-2 bg-white/5 border border-white/10 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500/50 w-48"
          />
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="space-y-3">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-12 bg-gray-700/30 rounded-lg animate-pulse" />
          ))}
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="text-center py-8 text-red-400">
          <XCircleIcon className="h-10 w-10 mx-auto mb-2 opacity-50" />
          <p className="text-sm">{error}</p>
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && filteredGroups.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <GlobeAltIcon className="h-10 w-10 mx-auto mb-2 opacity-50" />
          <p className="text-sm">
            {searchQuery ? 'No domains match your search' : 'No domains configured'}
          </p>
        </div>
      )}

      {/* Domain Groups */}
      {!loading && !error && filteredGroups.length > 0 && (
        <>
          <div className="space-y-2">
            <AnimatePresence>
              {displayedGroups.map((group, index) => (
                <motion.div
                  key={group.baseName}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ delay: index * 0.03 }}
                >
                  <DomainGroup
                    main={group.main}
                    children={group.children}
                    websiteStatus={websiteStatus}
                    onDomainClick={handleDomainClick}
                  />
                </motion.div>
              ))}
            </AnimatePresence>
          </div>

          {/* Show More/Less */}
          {hasMore && (
            <button
              onClick={() => setShowAll(!showAll)}
              className="flex items-center justify-center gap-2 w-full mt-4 py-2 text-sm text-gray-400 hover:text-white transition-colors"
            >
              {showAll ? (
                <>
                  <ChevronUpIcon className="h-4 w-4" />
                  Show Less
                </>
              ) : (
                <>
                  <ChevronDownIcon className="h-4 w-4" />
                  Show All ({filteredGroups.length} sites)
                </>
              )}
            </button>
          )}
        </>
      )}
    </motion.div>
  );
}
