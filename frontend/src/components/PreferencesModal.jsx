import { useState, useEffect } from 'react';
import { updatePreferences, getUserProfile } from '../lib/api';
import { useAuth0 } from '@auth0/auth0-react';

const PREFERENCE_LABELS = {
    price_sensitivity: { label: 'Price Sensitivity', emoji: '💰', description: 'Higher = prefer cheaper options' },
    quality: { label: 'Quality', emoji: '⭐', description: 'Higher = prioritize quality' },
    eco_friendly: { label: 'Eco-Friendly', emoji: '🌱', description: 'Higher = prefer sustainable products' },
    brand_reputation: { label: 'Brand Reputation', emoji: '🏆', description: 'Higher = prefer well-known brands' },
    durability: { label: 'Durability', emoji: '🛡️', description: 'Higher = prioritize long-lasting products' }
};

const PreferencesModal = ({ isOpen, onClose }) => {
    const { getAccessTokenSilently } = useAuth0();
    const [preferences, setPreferences] = useState({
        price_sensitivity: 0.5,
        quality: 0.5,
        eco_friendly: 0.3,
        brand_reputation: 0.5,
        durability: 0.5
    });
    const [isSaving, setIsSaving] = useState(false);
    const [isLoading, setIsLoading] = useState(true);

    // Load current preferences on open
    useEffect(() => {
        if (isOpen) {
            loadPreferences();
        }
    }, [isOpen]);

    const loadPreferences = async () => {
        setIsLoading(true);
        try {
            const token = await getAccessTokenSilently();
            console.log('[PreferencesModal] Fetching user profile...');
            const profile = await getUserProfile(token);
            console.log('[PreferencesModal] Profile received:', profile);
            if (profile?.preferences) {
                console.log('[PreferencesModal] Setting preferences:', profile.preferences);
                setPreferences(prev => ({ ...prev, ...profile.preferences }));
            } else {
                console.log('[PreferencesModal] No preferences in profile, keeping defaults');
            }
        } catch (error) {
            console.error('[PreferencesModal] Failed to load preferences:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleSliderChange = (key, value) => {
        setPreferences(prev => ({ ...prev, [key]: parseFloat(value) }));
    };

    const handleSave = async () => {
        setIsSaving(true);
        try {
            const token = await getAccessTokenSilently();
            await updatePreferences(preferences, token);
            onClose();
        } catch (error) {
            console.error('Failed to save preferences:', error);
        } finally {
            setIsSaving(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in" onClick={onClose}>
            <div className="bg-[#121214] border border-white/10 rounded-2xl w-full max-w-lg overflow-hidden relative shadow-2xl" onClick={e => e.stopPropagation()}>
                {/* Header */}
                <div className="px-6 py-4 border-b border-white/10 flex items-center justify-between">
                    <h2 className="text-lg font-bold text-white flex items-center gap-2">
                        <span>⚙️</span> Global Preferences
                    </h2>
                    <button
                        onClick={onClose}
                        className="p-1.5 rounded-full hover:bg-white/10 text-gray-400 hover:text-white transition-colors"
                    >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                    </button>
                </div>

                {/* Content */}
                <div className="p-6 space-y-5">
                    <p className="text-sm text-gray-400 mb-4">
                        These preferences persist across sessions and influence how alternatives are ranked.
                    </p>

                    {isLoading ? (
                        <div className="flex items-center justify-center py-8">
                            <div className="w-6 h-6 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
                        </div>
                    ) : (
                        Object.entries(PREFERENCE_LABELS).map(([key, { label, emoji, description }]) => (
                            <div key={key} className="space-y-2">
                                <div className="flex items-center justify-between">
                                    <label className="text-sm font-medium text-white flex items-center gap-2">
                                        <span>{emoji}</span> {label}
                                    </label>
                                    <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">
                                        {Math.round((preferences[key] || 0.5) * 100)}%
                                    </span>
                                </div>
                                <input
                                    type="range"
                                    min="0"
                                    max="1"
                                    step="0.05"
                                    value={preferences[key] || 0.5}
                                    onChange={(e) => handleSliderChange(key, e.target.value)}
                                    className="w-full h-2 bg-white/10 rounded-lg appearance-none cursor-pointer accent-emerald-500"
                                />
                                <p className="text-[10px] text-gray-500">{description}</p>
                            </div>
                        ))
                    )}
                </div>

                {/* Footer */}
                <div className="px-6 py-4 border-t border-white/10 flex items-center justify-end gap-3">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 text-sm font-medium text-gray-400 hover:text-white transition-colors"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleSave}
                        disabled={isSaving || isLoading}
                        className="px-5 py-2 text-sm font-semibold bg-emerald-500 hover:bg-emerald-600 text-black rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                        {isSaving ? (
                            <>
                                <div className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin" />
                                Saving...
                            </>
                        ) : (
                            'Save Preferences'
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default PreferencesModal;
