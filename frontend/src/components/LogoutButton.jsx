import { useAuth0 } from '@auth0/auth0-react';
import React from 'react';

const LogoutButton = () => {
  const { logout } = useAuth0();

  return (
    <button
      onClick={() => logout({ logoutParams: { returnTo: window.location.origin } })}
      className="px-4 py-1.5 text-xs font-medium text-gray-400 hover:text-white transition-colors border border-transparent hover:border-white/10 rounded-full"
    >
      Log Out
    </button>
  );
};

export default LogoutButton;
