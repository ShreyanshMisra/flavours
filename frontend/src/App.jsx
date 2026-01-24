/**
 * Flavor Pairing Explorer App
 */

import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { Home, Ingredient, Compare, Explore } from './pages';
import './App.css';

function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <nav className="navbar">
          <Link to="/" className="nav-brand">
            Flavor Pairing
          </Link>

          <div className="nav-links">
            <Link to="/">Home</Link>
            <Link to="/compare">Compare</Link>
            <Link to="/explore">Explore</Link>
          </div>
        </nav>

        <main className="main-content">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/ingredient/:id" element={<Ingredient />} />
            <Route path="/compare" element={<Compare />} />
            <Route path="/explore" element={<Explore />} />
          </Routes>
        </main>

        <footer className="footer">
          <p>
            Data sourced from{' '}
            <a
              href="https://cosylab.iiitd.edu.in/flavordb/"
              target="_blank"
              rel="noopener noreferrer"
            >
              FlavorDB
            </a>
          </p>
        </footer>
      </div>
    </BrowserRouter>
  );
}

export default App;
