"use client";
import { useState, useEffect } from "react";
import AaharSplashScreen from "./AaharSplashScreen";
import AaharWelcomeScreen from "./AaharWelcomeScreen";
import AaharOnboardingForm from "./AaharOnboardingForm";
import AaharBottomNav from "./AaharBottomNav";
import AaharHomeTab from "./AaharHomeTab";
import AaharMyPlanTab from "./AaharMyPlanTab";
import AaharGroceryTab from "./AaharGroceryTab";
import AaharProfileTab from "./AaharProfileTab";
import FoodChatbot from "./FoodChatbot";

export default function AaharDashboard() {
    const [screen, setScreen] = useState("splash"); // splash | welcome | onboarding | dashboard
    const [activeTab, setActiveTab] = useState("home");
    const [user, setUser] = useState(null);
    const [token, setToken] = useState(null);
    const [showChatbot, setShowChatbot] = useState(false);

    // Check for existing session on mount
    useEffect(() => {
        const savedToken = localStorage.getItem("aa_token");
        const savedUser = localStorage.getItem("aa_user");

        if (savedToken && savedUser) {
            const userData = JSON.parse(savedUser);
            setToken(savedToken);
            setUser(userData);
            // If profile is complete, go to dashboard, else onboarding
            setScreen(userData.profile_complete ? "dashboard" : "onboarding");
        } else {
            setScreen("welcome");
        }
    }, []);

    const handleAuth = (userData, authToken) => {
        setUser(userData);
        setToken(authToken);
        // Check if profile is complete
        if (userData.profile_complete) {
            setScreen("dashboard");
        } else {
            setScreen("onboarding");
        }
    };

    const handleSignOut = () => {
        localStorage.removeItem("aa_token");
        localStorage.removeItem("aa_user");
        setUser(null);
        setToken(null);
        setScreen("welcome");
    };

    const handleOnboardingComplete = () => {
        // Refresh user from localStorage to get updated profile_complete status
        const updatedUser = JSON.parse(localStorage.getItem("aa_user"));
        if (updatedUser) {
            setUser(updatedUser);
        }
        setScreen("dashboard");
    };

    const handleEditProfile = () => {
        // Re-open onboarding form in edit mode
        setScreen("onboarding");
    };

    // Splash screen
    if (screen === "splash") {
        return <AaharSplashScreen onDone={() => setScreen("welcome")} />;
    }

    // Welcome screen (login/register)
    if (screen === "welcome") {
        return <AaharWelcomeScreen onAuth={handleAuth} />;
    }

    // Onboarding form (first-time user)
    if (screen === "onboarding") {
        return <AaharOnboardingForm onComplete={handleOnboardingComplete} />;
    }

    // Main dashboard
    if (screen === "dashboard" && user) {
        return (
            <div className="fixed inset-0 flex flex-col bg-warm-cream">
                {/* Main content area */}
                <div className="flex-1 overflow-y-auto pb-28 max-w-md mx-auto w-full">
                    {/* Tab content */}
                    {activeTab === "home" && <AaharHomeTab user={user} token={token} />}
                    {activeTab === "plan" && <AaharMyPlanTab token={token} />}
                    {activeTab === "grocery" && <AaharGroceryTab />}
                    {activeTab === "profile" && (
                        <AaharProfileTab
                            user={user}
                            token={token}
                            onSignOut={handleSignOut}
                            onEditProfile={handleEditProfile}
                        />
                    )}
                </div>

                {/* Bottom Navigation */}
                <AaharBottomNav
                    activeTab={activeTab}
                    onTabChange={setActiveTab}
                    onChatbotClick={() => setShowChatbot(!showChatbot)}
                />

                {/* Chatbot Component */}
                <FoodChatbot 
                    isOpen={showChatbot} 
                    onClose={() => setShowChatbot(false)}
                    token={token}
                />
            </div>
        );
    }

    return null;
}
