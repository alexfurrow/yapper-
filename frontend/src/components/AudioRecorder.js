const API_URL = import.meta.env.VITE_API_URL;
const response = await fetch(`${API_URL}/api/audio/api`, {
  method: 'POST',
  body: formData
}); 