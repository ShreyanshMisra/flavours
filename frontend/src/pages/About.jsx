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
        <div className="how-it-works">
          <div className="concept">
            <h3>Flavor Compounds</h3>
            <p>
              Every ingredient contains molecules that contribute to its taste and aroma.
              These flavor compounds are the building blocks of how we perceive food.
            </p>
          </div>

          <div className="concept">
            <h3>Shared Chemistry</h3>
            <p>
              Ingredients that share key flavor compounds tend to pair well together,
              creating harmonious taste combinations that complement each other.
            </p>
          </div>

          <div className="concept">
            <h3>Knowledge Graph</h3>
            <p>
              We model ingredients and compounds as a graph database, enabling discovery
              of unexpected pairings like strawberry + balsamic or chocolate + blue cheese.
            </p>
          </div>
        </div>
      </section>

      <section className="about-section">
        <h2>Tech Stack</h2>
        <ul className="tech-list">
          <li>Neo4j Graph Database</li>
          <li>React Frontend</li>
          <li>FastAPI Backend</li>
          <li>D3.js Graph Visualization</li>
        </ul>
      </section>

      <section className="about-section">
        <h2>References</h2>
        <ul className="references-list">
          <li>
            <a href="https://cosylab.iiitd.edu.in/flavordb/" target="_blank" rel="noopener noreferrer">
              FlavorDB
            </a>
            {' '}- Primary data source for flavor compounds mapped to ingredients
          </li>
          <li>
            <a href="https://foodb.ca/" target="_blank" rel="noopener noreferrer">
              FooDB
            </a>
            {' '}- Supplementary food composition data
          </li>
          <li>
            <a href="https://www.nature.com/articles/srep00196" target="_blank" rel="noopener noreferrer">
              Ahn et al., "Flavor network and the principles of food pairing" (Scientific Reports, 2011)
            </a>
            {' '}- Foundational research on food pairing
          </li>
        </ul>
      </section>
    </div>
  );
}

export default About;
