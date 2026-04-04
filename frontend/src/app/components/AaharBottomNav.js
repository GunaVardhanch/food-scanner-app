"use client";

export default function AaharBottomNav({ activeTab, onTabChange, onChatbotClick }) {
    const tabs = [
        { id: "home", label: "Home", icon: "🏠" },
        { id: "plan", label: "My Plan", icon: "📅" },
        { id: "grocery", label: "Grocery", icon: "🛒" },
        { id: "profile", label: "Profile", icon: "👤" },
    ];

    return (
        <nav className="fixed bottom-0 left-0 right-0 z-40 flex justify-center pointer-events-none">
            {/* Main nav bar */}
            <div className="w-full max-w-md bg-white border-t border-slate-200 px-6 py-3 flex justify-between items-center pointer-events-auto rounded-t-2xl shadow-lg">
                {tabs.map(tab => (
                    <button
                        key={tab.id}
                        onClick={() => onTabChange(tab.id)}
                        className={`flex flex-col items-center gap-1.5 transition-all ${
                            activeTab === tab.id
                                ? "text-accent"
                                : "text-slate-400 hover:text-slate-500"
                        }`}
                    >
                        <div className="text-xl">{tab.icon}</div>
                        <span className="text-[8px] font-medium uppercase tracking-wide\">{tab.label}</span>
                    </button>
                ))}
            </div>

            {/* Floating action button */}
            <button
                onClick={onChatbotClick}
                className="absolute bottom-14 w-16 h-16 bg-accent hover:bg-accent-dark rounded-full flex items-center justify-center text-slate-900 border-4 border-white shadow-lg active:scale-90 transition-all pointer-events-auto z-50"
            >
                <span className="text-2xl">💬</span>
            </button>
        </nav>
    );
}
