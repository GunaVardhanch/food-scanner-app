"use client";

export default function AaharGroceryTab() {
    const items = [
        { category: "Vegetables", emoji: "🥬", items: [
            { name: "Tomatoes", qty: "1 kg", cost: 40 },
            { name: "Onions", qty: "2 kg", cost: 60 },
            { name: "Garlic", qty: "250g", cost: 30 },
            { name: "Ginger", qty: "200g", cost: 40 },
            { name: "Green Chili", qty: "100g", cost: 20 },
        ]},
        { category: "Grains & Pulses", emoji: "🌾", items: [
            { name: "Rice", qty: "5 kg", cost: 200 },
            { name: "Red Lentils", qty: "2 kg", cost: 180 },
            { name: "Chickpeas", qty: "1 kg", cost: 100 },
            { name: "Wheat Flour", qty: "5 kg", cost: 150 },
        ]},
        { category: "Dairy", emoji: "🥛", items: [
            { name: "Milk", qty: "2 L", cost: 100 },
            { name: "Yogurt", qty: "500g", cost: 50 },
            { name: "Paneer", qty: "500g", cost: 150 },
        ]},
        { category: "Spices", emoji: "🧂", items: [
            { name: "Turmeric Powder", qty: "100g", cost: 30 },
            { name: "Cumin Seeds", qty: "100g", cost: 40 },
            { name: "Coriander Seeds", qty: "100g", cost: 35 },
            { name: "Mustard Seeds", qty: "100g", cost: 50 },
        ]},
        { category: "Fruits", emoji: "🍎", items: [
            { name: "Bananas", qty: "1 dozen", cost: 60 },
            { name: "Apples", qty: "1 kg", cost: 120 },
            { name: "Oranges", qty: "1 kg", cost: 80 },
        ]},
    ];

    const totalCost = items.reduce((sum, cat) => 
        sum + cat.items.reduce((catSum, item) => catSum + item.cost, 0), 0
    );

    const handleShare = () => {
        const listText = items.map(cat =>
            `${cat.emoji} ${cat.category}\n${cat.items.map(i => `• ${i.name} - ${i.qty} (₹${i.cost})`).join("\n")}`
        ).join("\n\n");
        
        const fullText = `MA-Shabari - Weekly Grocery List\n\n${listText}\n\nTotal: ₹${totalCost}`;
        
        if (navigator.share) {
            navigator.share({ title: "Grocery List", text: fullText });
        } else {
            navigator.clipboard.writeText(fullText);
            alert("List copied to clipboard!");
        }
    };

    return (
        <div className="px-5 py-5">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-black text-dark-navy mb-2">Weekly Grocery</h1>
                <p className="text-sm text-slate-500 font-medium">Total: ₹{totalCost}</p>
            </div>

            {/* Categories */}
            <div className="space-y-6">
                {items.map(categoryItem => (
                    <div key={categoryItem.category}>
                        <h2 className="text-lg font-black text-dark-navy mb-3 flex items-center gap-2">
                            <span className="text-2xl">{categoryItem.emoji}</span>
                            {categoryItem.category}
                        </h2>
                        <div className="space-y-2">
                            {categoryItem.items.map(item => (
                                <div key={item.name} className="bg-white rounded-xl p-3 border border-slate-100 flex items-center justify-between hover:shadow-md transition-shadow">
                                    <div className="flex-1">
                                        <p className="text-sm font-bold text-dark-navy">{item.name}</p>
                                        <p className="text-xs text-slate-500">{item.qty}</p>
                                    </div>
                                    <span className="font-black text-saffron">₹{item.cost}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                ))}
            </div>

            {/* Bottom summary */}
            <div className="fixed bottom-24 left-0 right-0 px-5 pb-4 max-w-md mx-auto">
                <button
                    onClick={handleShare}
                    className="w-full h-14 bg-gradient-to-r from-saffron to-india-green text-white rounded-xl font-black text-sm uppercase tracking-widest active:scale-95 transition-all"
                >
                    📋 Share List
                </button>
            </div>
        </div>
    );
}
