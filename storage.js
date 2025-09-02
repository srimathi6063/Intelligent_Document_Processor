// storage.js

// Save data (object) to localStorage as JSON string
export function saveToStorage(key, data) {
  try {
    const jsonData = JSON.stringify(data);
    localStorage.setItem(key, jsonData);
  } catch (e) {
    console.error(`Failed to save ${key} to localStorage:`, e);
  }
}

// Load JSON data from localStorage and parse it
export function loadFromStorage(key) {
  try {
    const jsonData = localStorage.getItem(key);
    if (!jsonData) return null;
    return JSON.parse(jsonData);
  } catch (e) {
    console.error(`Failed to load ${key} from localStorage:`, e);
    return null;
  }
}

// Remove an item from localStorage
export function removeFromStorage(key) {
  try {
    localStorage.removeItem(key);
  } catch (e) {
    console.error(`Failed to remove ${key} from localStorage:`, e);
  }
}
