import React, { useEffect, useState } from 'react';
import { MenuCategory, MenuItem } from '../types';
import { Utensils, AlertTriangle, Flame } from 'lucide-react';

export const RestaurantMenu: React.FC = () => {
  const [categories, setCategories] = useState<MenuCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAllergen, setSelectedAllergen] = useState<string>('all');

  useEffect(() => {
    fetch('http://localhost:8005/api/menu')
      .then((res) => res.json())
      .then((data) => {
        setCategories(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to load menu", err);
        setLoading(false);
      });
  }, []);

  return (
    <div className="bg-stone-900 border border-stone-800 rounded-2xl p-6 shadow-xl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-4 border-b border-stone-800">
        <div>
          <div className="flex items-center gap-2">
            <Utensils className="w-5 h-5 text-amber-500" />
            <h3 className="text-xl font-semibold text-white tracking-wide">Culinary Hearth Menu</h3>
          </div>
          <p className="text-xs text-stone-400 mt-1">
            Ingredients sourced sustainably; prepared on our white-oak open embers.
          </p>
        </div>

        {/* Dietary & Allergen Filter */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-stone-400">Highlight Allergens:</span>
          <select
            value={selectedAllergen}
            onChange={(e) => setSelectedAllergen(e.target.value)}
            className="px-3 py-1.5 bg-stone-950 border border-stone-800 text-xs text-stone-300 rounded-lg focus:outline-none focus:border-amber-500"
          >
            <option value="all">Show All Items</option>
            <option value="Gluten">Contains Gluten</option>
            <option value="Dairy">Contains Dairy</option>
            <option value="Shellfish">Contains Shellfish</option>
            <option value="Tree Nuts">Contains Tree Nuts</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="py-12 text-center text-xs text-stone-500">Loading seasonal menu...</div>
      ) : (
        <div className="space-y-8">
          {categories.map((category) => (
            <div key={category.id}>
              <h4 className="text-sm font-semibold text-amber-400 uppercase tracking-wider mb-4 border-l-2 border-amber-500 pl-3">
                {category.name}
              </h4>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {category.items.map((item: MenuItem) => {
                  const hasSelectedAllergen = selectedAllergen !== 'all' && item.allergens.includes(selectedAllergen);

                  return (
                    <div
                      key={item.id}
                      className={`p-4 rounded-xl border transition ${
                        hasSelectedAllergen
                          ? 'bg-rose-950/20 border-rose-800/60'
                          : 'bg-stone-950/60 border-stone-800/80 hover:border-stone-700'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <h5 className="text-sm font-medium text-white flex items-center gap-1.5">
                          {item.name}
                          {item.spicy_level > 0 && <Flame className="w-3.5 h-3.5 text-rose-500" />}
                        </h5>
                        <span className="text-sm font-semibold text-amber-300">${item.price.toFixed(2)}</span>
                      </div>

                      <p className="text-xs text-stone-400 mt-1.5 leading-relaxed">{item.description}</p>

                      {/* Dietary Badges */}
                      <div className="flex flex-wrap items-center gap-1.5 mt-3">
                        {item.is_vegan && (
                          <span className="px-2 py-0.5 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-md text-[10px] font-medium">
                            Vegan
                          </span>
                        )}
                        {item.is_vegetarian && !item.is_vegan && (
                          <span className="px-2 py-0.5 bg-green-500/10 text-green-400 border border-green-500/20 rounded-md text-[10px] font-medium">
                            Vegetarian
                          </span>
                        )}
                        {item.is_gluten_free && (
                          <span className="px-2 py-0.5 bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded-md text-[10px] font-medium">
                            Gluten-Free
                          </span>
                        )}

                        {/* Allergen Tag */}
                        {item.allergens.length > 0 && (
                          <span className="px-2 py-0.5 bg-amber-500/10 text-amber-300/80 border border-amber-500/20 rounded-md text-[10px]">
                            Contains: {item.allergens.join(', ')}
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}

          {/* Kitchen Cross-Contamination Notice */}
          <div className="p-4 bg-stone-950 border border-stone-800 rounded-xl text-xs text-stone-400 flex items-start gap-3 mt-6">
            <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
            <div>
              <strong className="text-stone-300">Kitchen Allergen Advisory:</strong> While we offer gluten-free and vegan preparations, our kitchen operates open wood-fired hearths and shared prep tables where shellfish, dairy, gluten, and tree nuts are present. Severe allergies should be communicated directly to management.
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
