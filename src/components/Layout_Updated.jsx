// This file shows the changes needed to integrate TierBadge into the Layout
// Add this import at the top:
import TierBadge from './billing/TierBadge';

// In the user section (around line 266), replace the existing user info section with:

{/* User Info with Tier Badge and Logout */}
<div className="px-2 mb-4">
  <div className="border-t border-white/10 pt-4">
    {userInfo.username && (
      <>
        {/* User Profile Section */}
        <div className={`mb-3 px-2`}>
          <div className="flex items-center gap-2 mb-2">
            <UserCircleIcon className={`h-5 w-5 ${
              currentTheme === 'unicorn' ? 'text-purple-200' :
              currentTheme === 'light' ? 'text-gray-600' : 'text-gray-400'
            }`} />
            <span className={`text-sm font-medium ${
              currentTheme === 'unicorn' ? 'text-purple-100' :
              currentTheme === 'light' ? 'text-gray-700' : 'text-gray-300'
            }`}>
              {userInfo.username}
            </span>
          </div>

          {/* Tier Badge - compact variant for sidebar */}
          <div className="mt-2">
            <TierBadge
              tier={userInfo.subscription_tier || 'free'}
              variant="compact"
              showUsage={false}
            />
          </div>
        </div>

        {/* User Settings Link */}
        <Link
          to="/admin/user-settings"
          className={`w-full flex items-center gap-2 px-3 py-2 mb-2 text-sm font-medium rounded-lg transition-all duration-200 ${
            location.pathname === '/admin/user-settings'
              ? currentTheme === 'unicorn'
                ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white'
                : currentTheme === 'light'
                ? 'bg-blue-100 text-blue-700'
                : 'bg-slate-700 text-blue-400'
              : currentTheme === 'unicorn'
                ? 'text-purple-200 hover:bg-white/10'
                : currentTheme === 'light'
                ? 'text-gray-600 hover:bg-gray-100'
                : 'text-gray-300 hover:bg-gray-700'
          }`}
        >
          <CogIcon className="h-5 w-5" />
          Account Settings
        </Link>
      </>
    )}

    {/* Logout Button */}
    <button
      onClick={handleLogout}
      className={`w-full flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-lg transition-all duration-200 ${
        currentTheme === 'unicorn'
          ? 'text-red-300 hover:bg-red-900/20 hover:text-red-200'
          : currentTheme === 'light'
          ? 'text-red-600 hover:bg-red-50 hover:text-red-700'
          : 'text-red-400 hover:bg-red-900/20 hover:text-red-300'
      }`}
    >
      <ArrowRightOnRectangleIcon className="h-5 w-5" />
      Logout
    </button>
  </div>
</div>

// Also, you need to load the user's subscription tier when the Layout component mounts.
// Add this useEffect after the existing useEffects:

useEffect(() => {
  // Load user subscription tier
  const loadUserTier = async () => {
    if (userInfo.email) {
      try {
        const response = await fetch(`/api/v1/user/tier?email=${userInfo.email}`);
        if (response.ok) {
          const data = await response.json();
          // Update userInfo in localStorage with tier
          const updatedUserInfo = { ...userInfo, subscription_tier: data.tier };
          localStorage.setItem('userInfo', JSON.stringify(updatedUserInfo));
        }
      } catch (error) {
        console.error('Failed to load user tier:', error);
      }
    }
  };

  loadUserTier();
}, []);
