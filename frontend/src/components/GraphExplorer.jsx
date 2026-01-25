/**
 * GraphExplorer Component
 *
 * D3.js force-directed graph visualization for ingredient relationships.
 */

import { useEffect, useRef, useCallback } from 'react';
import * as d3 from 'd3';
import { getCategoryColor } from './IngredientCard';
import './GraphExplorer.css';

export function GraphExplorer({ data, onNodeClick, width = 800, height = 600 }) {
  const svgRef = useRef(null);
  const simulationRef = useRef(null);

  const createGraph = useCallback(() => {
    if (!data?.nodes?.length || !svgRef.current) return;

    const svg = d3.select(svgRef.current);

    // Clear previous content
    svg.selectAll('*').remove();

    // Create container group for zoom
    const g = svg.append('g');

    // Set up zoom behavior
    const zoom = d3.zoom()
      .scaleExtent([0.3, 3])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });

    svg.call(zoom);

    // Create a copy of nodes and links for simulation
    const nodes = data.nodes.map(d => ({ ...d }));
    const links = data.links.map(d => ({ ...d }));

    // Create force simulation
    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links)
        .id(d => d.id)
        .distance(d => 150 - (d.score || 0.5) * 50)
        .strength(d => (d.score || 0.5) * 0.5))
      .force('charge', d3.forceManyBody()
        .strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(40));

    simulationRef.current = simulation;

    // Get border color for links (theme-aware)
    const borderColor = getComputedStyle(document.documentElement)
      .getPropertyValue('--color-text-muted').trim() || '#999';

    // Draw links - increased thickness variation for visibility
    const link = g.append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke', borderColor)
      .attr('stroke-opacity', d => 0.3 + (d.score || 0.5) * 0.5)
      .attr('stroke-width', d => 1 + (d.score || 0.5) * 5);

    // Draw nodes
    const node = g.append('g')
      .attr('class', 'nodes')
      .selectAll('g')
      .data(nodes)
      .join('g')
      .attr('class', 'node')
      .call(drag(simulation));

    // Get CSS variable value for text color (theme-aware)
    const textColor = getComputedStyle(document.documentElement)
      .getPropertyValue('--color-text-secondary').trim() || '#555';
    const primaryColor = getComputedStyle(document.documentElement)
      .getPropertyValue('--color-primary').trim() || '#4a90d9';

    // Node circles
    node.append('circle')
      .attr('r', d => d.id === data.nodes[0]?.id ? 25 : 18)
      .attr('fill', d => d.id === data.nodes[0]?.id ? primaryColor : getCategoryColor(d.category))
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .on('click', (event, d) => {
        event.stopPropagation();
        if (onNodeClick) onNodeClick(d);
      })
      .on('mouseover', function() {
        d3.select(this).attr('stroke-width', 4);
      })
      .on('mouseout', function() {
        d3.select(this).attr('stroke-width', 2);
      });

    // Node labels
    node.append('text')
      .text(d => d.name)
      .attr('x', 0)
      .attr('y', d => (d.id === data.nodes[0]?.id ? 25 : 18) + 14)
      .attr('text-anchor', 'middle')
      .attr('font-size', d => d.id === data.nodes[0]?.id ? '13px' : '11px')
      .attr('font-weight', d => d.id === data.nodes[0]?.id ? '600' : '400')
      .attr('fill', textColor);

    // Update positions on tick
    simulation.on('tick', () => {
      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);

      node.attr('transform', d => `translate(${d.x},${d.y})`);
    });

    // Center the view
    svg.call(zoom.transform, d3.zoomIdentity.translate(0, 0).scale(1));

  }, [data, width, height, onNodeClick]);

  useEffect(() => {
    createGraph();

    return () => {
      if (simulationRef.current) {
        simulationRef.current.stop();
      }
    };
  }, [createGraph]);

  // Drag behavior
  function drag(simulation) {
    function dragstarted(event) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      event.subject.fx = event.subject.x;
      event.subject.fy = event.subject.y;
    }

    function dragged(event) {
      event.subject.fx = event.x;
      event.subject.fy = event.y;
    }

    function dragended(event) {
      if (!event.active) simulation.alphaTarget(0);
      event.subject.fx = null;
      event.subject.fy = null;
    }

    return d3.drag()
      .on('start', dragstarted)
      .on('drag', dragged)
      .on('end', dragended);
  }

  return (
    <div className="graph-explorer">
      <svg
        ref={svgRef}
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
      />
      <div className="graph-controls">
        <button
          onClick={() => {
            const svg = d3.select(svgRef.current);
            const zoom = d3.zoom();
            svg.transition().duration(500).call(
              zoom.transform,
              d3.zoomIdentity.translate(width / 2, height / 2).scale(1).translate(-width / 2, -height / 2)
            );
          }}
        >
          Reset View
        </button>
      </div>
    </div>
  );
}

export default GraphExplorer;
