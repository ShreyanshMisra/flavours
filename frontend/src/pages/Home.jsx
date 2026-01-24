/**
 * Home Page
 *
 * Main landing page with knowledge graph visualization and stats.
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import * as d3 from 'd3';
import { useStats } from '../hooks/useApi';
import { getCategoryColor } from '../components/IngredientCard';
import api from '../api/client';
import './Home.css';

export function Home() {
  const navigate = useNavigate();
  const { data: stats } = useStats();
  const svgRef = useRef(null);
  const containerRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 500 });
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(true);

  // Fetch graph data on mount
  useEffect(() => {
    const fetchGraph = async () => {
      try {
        const randomIng = await api.getRandomIngredient();
        const data = await api.getGraphData(randomIng.id, { minScore: 0.3, limit: 25 });
        setGraphData(data);
      } catch (err) {
        console.error('Failed to load graph:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchGraph();
  }, []);

  // Handle resize
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        setDimensions({
          width: rect.width,
          height: Math.max(400, window.innerHeight - 280)
        });
      }
    };

    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  // D3 Graph Rendering
  const createGraph = useCallback(() => {
    if (!graphData?.nodes?.length || !svgRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const { width, height } = dimensions;
    const g = svg.append('g');

    // Zoom behavior
    const zoom = d3.zoom()
      .scaleExtent([0.3, 3])
      .on('zoom', (event) => g.attr('transform', event.transform));

    svg.call(zoom);

    const nodes = graphData.nodes.map(d => ({ ...d }));
    const links = graphData.links.map(d => ({ ...d }));

    // Force simulation
    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links)
        .id(d => d.id)
        .distance(100)
        .strength(d => (d.score || 0.5) * 0.3))
      .force('charge', d3.forceManyBody().strength(-200))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(35));

    // Links
    const link = g.append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke', 'var(--color-border)')
      .attr('stroke-opacity', d => 0.3 + (d.score || 0.5) * 0.4)
      .attr('stroke-width', d => 1 + (d.score || 0.5) * 2);

    // Nodes
    const node = g.append('g')
      .attr('class', 'nodes')
      .selectAll('g')
      .data(nodes)
      .join('g')
      .attr('class', 'node')
      .style('cursor', 'pointer')
      .call(d3.drag()
        .on('start', (event) => {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          event.subject.fx = event.subject.x;
          event.subject.fy = event.subject.y;
        })
        .on('drag', (event) => {
          event.subject.fx = event.x;
          event.subject.fy = event.y;
        })
        .on('end', (event) => {
          if (!event.active) simulation.alphaTarget(0);
          event.subject.fx = null;
          event.subject.fy = null;
        }));

    node.append('circle')
      .attr('r', d => d.id === nodes[0]?.id ? 22 : 16)
      .attr('fill', d => getCategoryColor(d.category))
      .attr('stroke', 'var(--color-bg-elevated)')
      .attr('stroke-width', 2)
      .on('click', (event, d) => {
        event.stopPropagation();
        navigate(`/ingredient/${d.id}`);
      })
      .on('mouseover', function() {
        d3.select(this).attr('stroke-width', 3);
      })
      .on('mouseout', function() {
        d3.select(this).attr('stroke-width', 2);
      });

    node.append('text')
      .text(d => d.name)
      .attr('x', 0)
      .attr('y', d => (d.id === nodes[0]?.id ? 22 : 16) + 12)
      .attr('text-anchor', 'middle')
      .attr('font-size', d => d.id === nodes[0]?.id ? '11px' : '10px')
      .attr('font-weight', d => d.id === nodes[0]?.id ? '600' : '400')
      .attr('fill', 'var(--color-text-secondary)')
      .style('pointer-events', 'none');

    simulation.on('tick', () => {
      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);
      node.attr('transform', d => `translate(${d.x},${d.y})`);
    });

    // Center view
    svg.call(zoom.transform, d3.zoomIdentity.translate(0, 0).scale(1));

    return () => simulation.stop();
  }, [graphData, dimensions, navigate]);

  useEffect(() => {
    createGraph();
  }, [createGraph]);

  const handleRefresh = async () => {
    setLoading(true);
    try {
      const randomIng = await api.getRandomIngredient();
      const data = await api.getGraphData(randomIng.id, { minScore: 0.3, limit: 25 });
      setGraphData(data);
    } catch (err) {
      console.error('Failed to load graph:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="home-page">
      <header className="home-header">
        <h1>Flavour Pairing Knowledge Graph</h1>
        <p>Discover ingredient pairings through shared flavor compounds</p>
      </header>

      {stats && (
        <div className="stats-row">
          <div className="stat-item">
            <span className="stat-value">{stats.ingredients.toLocaleString()}</span>
            <span className="stat-label">Ingredients</span>
          </div>
          <div className="stat-divider" />
          <div className="stat-item">
            <span className="stat-value">{stats.compounds.toLocaleString()}</span>
            <span className="stat-label">Compounds</span>
          </div>
          <div className="stat-divider" />
          <div className="stat-item">
            <span className="stat-value">{stats.pairings.toLocaleString()}</span>
            <span className="stat-label">Pairings</span>
          </div>
        </div>
      )}

      <div className="graph-container" ref={containerRef}>
        {loading ? (
          <div className="graph-loading">
            <div className="spinner" aria-label="Loading graph" />
            <span>Loading knowledge graph...</span>
          </div>
        ) : (
          <>
            <svg
              ref={svgRef}
              width={dimensions.width}
              height={dimensions.height}
              viewBox={`0 0 ${dimensions.width} ${dimensions.height}`}
              role="img"
              aria-label="Interactive knowledge graph showing ingredient relationships"
            />
            <div className="graph-actions">
              <button onClick={handleRefresh} className="refresh-btn" aria-label="Load different ingredient graph">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                  <path d="M23 4v6h-6M1 20v-6h6" />
                  <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15" />
                </svg>
                New Graph
              </button>
            </div>
            <p className="graph-hint">Click any node to explore. Drag to rearrange. Scroll to zoom.</p>
          </>
        )}
      </div>
    </div>
  );
}

export default Home;
