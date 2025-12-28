import React, { useState, useEffect } from 'react';
import { XMarkIcon, ArrowLeftIcon, ArrowRightIcon } from '@heroicons/react/24/outline';

const tourSteps = [
  {
    id: 'welcome',
    title: 'Welcome to UC-1 Pro Admin Dashboard! 🦄',
    content: 'This dashboard helps you manage your AI infrastructure, including models, services, and system resources.',
    target: null,
    position: 'center'
  },
  {
    id: 'dashboard',
    title: 'Dashboard Overview',
    content: 'The main dashboard shows your system status, active services, and quick stats. You can start/stop extensions and monitor GPU usage.',
    target: '[href="/"]',
    position: 'right'
  },
  {
    id: 'models',
    title: 'AI Model Management',
    content: 'Browse, download, and manage AI models from Hugging Face. Set retention policies and configure context sizes for optimal performance.',
    target: '[href="/models"]',
    position: 'right'
  },
  {
    id: 'services',
    title: 'Service Control',
    content: 'Monitor and control all your AI services. Start, stop, or restart services, and view their logs.',
    target: '[href="/services"]',
    position: 'right'
  },
  {
    id: 'system',
    title: 'System Monitoring',
    content: 'Keep track of CPU, GPU, memory, and disk usage in real-time. Essential for optimizing performance.',
    target: '[href="/system"]',
    position: 'right'
  },
  {
    id: 'network',
    title: 'Network Configuration',
    content: 'Configure network settings, connect to WiFi, and manage network interfaces.',
    target: '[href="/network"]',
    position: 'right'
  },
  {
    id: 'settings',
    title: 'System Settings',
    content: 'Configure system-wide settings, notifications, security, and backup schedules.',
    target: '[href="/settings"]',
    position: 'right'
  },
  {
    id: 'theme',
    title: 'Theme Switcher',
    content: 'Switch between Unicorn, Dark, and Light themes to match your preference!',
    target: '.border-t.border-white\\/10',
    position: 'top'
  }
];

export default function OnboardingTour({ onComplete }) {
  const [currentStep, setCurrentStep] = useState(0);
  const [isVisible, setIsVisible] = useState(false);
  const [targetRect, setTargetRect] = useState(null);

  useEffect(() => {
    // Check if user has completed onboarding
    const hasCompletedTour = localStorage.getItem('uc1-tour-completed');
    if (!hasCompletedTour) {
      setIsVisible(true);
    }
  }, []);

  useEffect(() => {
    if (isVisible && tourSteps[currentStep].target) {
      const element = document.querySelector(tourSteps[currentStep].target);
      if (element) {
        const rect = element.getBoundingClientRect();
        setTargetRect(rect);
        
        // Highlight the element
        element.classList.add('tour-highlight');
        
        return () => {
          element.classList.remove('tour-highlight');
        };
      }
    }
  }, [currentStep, isVisible]);

  const handleNext = () => {
    if (currentStep < tourSteps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      completeTour();
    }
  };

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const completeTour = () => {
    localStorage.setItem('uc1-tour-completed', 'true');
    setIsVisible(false);
    if (onComplete) onComplete();
  };

  const skipTour = () => {
    completeTour();
  };

  if (!isVisible) return null;

  const step = tourSteps[currentStep];
  const isCenter = step.position === 'center';

  const getTooltipPosition = () => {
    if (isCenter || !targetRect) {
      return {
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)'
      };
    }

    switch (step.position) {
      case 'right':
        return {
          top: targetRect.top + targetRect.height / 2 - 75,
          left: targetRect.right + 20
        };
      case 'left':
        return {
          top: targetRect.top + targetRect.height / 2 - 75,
          right: window.innerWidth - targetRect.left + 20
        };
      case 'top':
        return {
          bottom: window.innerHeight - targetRect.top + 20,
          left: targetRect.left + targetRect.width / 2,
          transform: 'translateX(-50%)'
        };
      case 'bottom':
        return {
          top: targetRect.bottom + 20,
          left: targetRect.left + targetRect.width / 2,
          transform: 'translateX(-50%)'
        };
      default:
        return {};
    }
  };

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black bg-opacity-50 z-[100]" onClick={skipTour} />
      
      {/* Spotlight for target element */}
      {targetRect && !isCenter && (
        <div
          className="fixed border-2 border-blue-500 rounded-lg z-[101]"
          style={{
            top: targetRect.top - 4,
            left: targetRect.left - 4,
            width: targetRect.width + 8,
            height: targetRect.height + 8,
            boxShadow: '0 0 0 9999px rgba(0, 0, 0, 0.5)'
          }}
        />
      )}
      
      {/* Tour tooltip */}
      <div
        className="fixed z-[102] bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6 max-w-md"
        style={getTooltipPosition()}
      >
        <div className="flex justify-between items-start mb-3">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            {step.title}
          </h3>
          <button
            onClick={skipTour}
            className="text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300"
          >
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>
        
        <p className="text-gray-600 dark:text-gray-300 mb-6">
          {step.content}
        </p>
        
        <div className="flex justify-between items-center">
          <div className="text-sm text-gray-500 dark:text-gray-400">
            Step {currentStep + 1} of {tourSteps.length}
          </div>
          
          <div className="flex gap-2">
            <button
              onClick={handlePrev}
              disabled={currentStep === 0}
              className="px-3 py-1 text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200 disabled:opacity-50"
            >
              <ArrowLeftIcon className="h-4 w-4" />
            </button>
            
            <button
              onClick={skipTour}
              className="px-3 py-1 text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200"
            >
              Skip
            </button>
            
            <button
              onClick={handleNext}
              className="px-4 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              {currentStep === tourSteps.length - 1 ? 'Finish' : 'Next'}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}