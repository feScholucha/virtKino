import React from 'react';

const DebugPanel = ({ data }) => {
  const { intencao, filtros_extraidos, filmes_encontrados, filme_selecionado } = data || {};

  return (
    <div className="debug-panel">
      <h2 style={{ color: '#00ff9d', borderBottom: '1px solid #444' }}>CÉREBRO.LOG</h2>

      <div className="debug-section">
        <span className="debug-label">INTENÇÃO DETECTADA</span>
        <div style={{ 
          fontWeight: 'bold', 
          color: intencao === 'filme' ? '#00ff9d' : '#bd00ff',
          fontSize: '1.2rem'
        }}>
          {intencao ? intencao.toUpperCase() : '---'}
        </div>
      </div>

      <div className="debug-section">
        <span className="debug-label">FILTROS EXTRAÍDOS (LLM)</span>
        <pre className="json-block">
          {JSON.stringify(filtros_extraidos || {}, null, 2)}
        </pre>
      </div>

      {intencao === 'filme' && (
        <div className="debug-section">
          <span className="debug-label">DADOS DO BANCO</span>
          <div className="json-block">
            Candidatos: {filmes_encontrados}<br/>
            Top 1: <span style={{color: '#f1fa8c'}}>{filme_selecionado}</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default DebugPanel;