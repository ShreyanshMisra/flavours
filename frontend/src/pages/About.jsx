/**
 * About Page
 *
 * Information about how the app works and tech stack.
 */

import './About.css';

export function About() {
  return (
    <div className="about-page">
      <header className="about-header">
        <h1>About</h1>
        <p>Learn how flavor pairing works and the technology behind this project</p>
      </header>

      <section className="about-section">
        <h2>How It Works</h2>
        <div className="info-grid">
          <article className="info-card">
            <div className="info-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                <circle cx="12" cy="12" r="10" />
                <path d="M12 6v6l4 2" />
              </svg>
            </div>
            <h3>Flavor Compounds</h3>
            <p>
              Every ingredient contains molecules that contribute to its taste and aroma.
              These flavor compounds are the building blocks of how we perceive food.
            </p>
          </article>

          <article className="info-card">
            <div className="info-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                <path d="M12 2L2 7l10 5 10-5-10-5z" />
                <path d="M2 17l10 5 10-5M2 12l10 5 10-5" />
              </svg>
            </div>
            <h3>Shared Chemistry</h3>
            <p>
              Ingredients that share key flavor compounds tend to pair well together,
              creating harmonious taste combinations that complement each other.
            </p>
          </article>

          <article className="info-card">
            <div className="info-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                <circle cx="12" cy="12" r="3" />
                <circle cx="19" cy="5" r="2" />
                <circle cx="5" cy="5" r="2" />
                <circle cx="19" cy="19" r="2" />
                <circle cx="5" cy="19" r="2" />
                <line x1="10" y1="10" x2="6.5" y2="6.5" />
                <line x1="14" y1="10" x2="17.5" y2="6.5" />
                <line x1="14" y1="14" x2="17.5" y2="17.5" />
                <line x1="10" y1="14" x2="6.5" y2="17.5" />
              </svg>
            </div>
            <h3>Knowledge Graph</h3>
            <p>
              We model ingredients and compounds as a graph database, enabling discovery
              of unexpected pairings like strawberry + balsamic or chocolate + blue cheese.
            </p>
          </article>
        </div>
      </section>

      <section className="about-section">
        <h2>Tech Stack</h2>
        <div className="tech-grid">
          <div className="tech-item">
            <div className="tech-logo neo4j">
              <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm0 3.6a8.4 8.4 0 110 16.8 8.4 8.4 0 010-16.8z"/>
                <circle cx="12" cy="12" r="3"/>
              </svg>
            </div>
            <div className="tech-info">
              <strong>Neo4j</strong>
              <span>Graph Database</span>
            </div>
          </div>

          <div className="tech-item">
            <div className="tech-logo react">
              <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                <circle cx="12" cy="12" r="2.139"/>
                <ellipse cx="12" cy="12" rx="11" ry="4.2" fill="none" stroke="currentColor" strokeWidth="1"/>
                <ellipse cx="12" cy="12" rx="11" ry="4.2" fill="none" stroke="currentColor" strokeWidth="1" transform="rotate(60 12 12)"/>
                <ellipse cx="12" cy="12" rx="11" ry="4.2" fill="none" stroke="currentColor" strokeWidth="1" transform="rotate(120 12 12)"/>
              </svg>
            </div>
            <div className="tech-info">
              <strong>React</strong>
              <span>Frontend Framework</span>
            </div>
          </div>

          <div className="tech-item">
            <div className="tech-logo d3">
              <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                <path d="M12 0L1.5 6v12L12 24l10.5-6V6L12 0zm0 3.5l7.5 4.3v8.4L12 20.5l-7.5-4.3V7.8L12 3.5z"/>
              </svg>
            </div>
            <div className="tech-info">
              <strong>D3.js</strong>
              <span>Graph Visualization</span>
            </div>
          </div>

          <div className="tech-item">
            <div className="tech-logo fastapi">
              <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                <path d="M12 0L3 4v8l9 4 9-4V4l-9-4zm0 2.18l6.75 3L12 8.18l-6.75-3L12 2.18zM5 6.5l6 2.67v7.16l-6-2.67V6.5zm14 0v7.16l-6 2.67V9.17l6-2.67z"/>
              </svg>
            </div>
            <div className="tech-info">
              <strong>FastAPI</strong>
              <span>Backend API</span>
            </div>
          </div>
        </div>
      </section>

      <section className="about-section">
        <h2>Data Source</h2>
        <p className="data-info">
          Ingredient and compound data sourced from{' '}
          <a href="https://cosylab.iiitd.edu.in/flavordb/" target="_blank" rel="noopener noreferrer">
            FlavorDB
          </a>
          , a database of flavor molecules and their associations with food ingredients.
        </p>
      </section>

      <section className="about-section">
        <h2>Open Source</h2>
        <p className="data-info">
          This project is open source. View the code, report issues, or contribute on{' '}
          <a href="https://github.com/shreyansh26/flavour-pairing-kg" target="_blank" rel="noopener noreferrer">
            GitHub
          </a>.
        </p>
      </section>
    </div>
  );
}

export default About;
