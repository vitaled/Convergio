import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/svelte';
import StreamingInterface from '$lib/components/StreamingInterface.svelte';
import RAGConfiguration from '$lib/components/RAGConfiguration.svelte';
import GraphFlowBuilder from '$lib/components/GraphFlowBuilder.svelte';
import HITLApprovalInterface from '$lib/components/HITLApprovalInterface.svelte';

describe('UI Core Components', () => {
  describe('StreamingInterface', () => {
    it('should render without errors', () => {
      const { container } = render(StreamingInterface, {
        props: {
          agentId: 'test-agent',
          sessionId: 'test-session'
        }
      });
      expect(container.querySelector('.streaming-interface')).toBeTruthy();
      expect(container.querySelector('.streaming-header')).toBeTruthy();
      expect(container.querySelector('.messages-container')).toBeTruthy();
      expect(container.querySelector('.input-container')).toBeTruthy();
    });
  });

  describe('RAGConfiguration', () => {
    it('should render without errors', () => {
      const { container } = render(RAGConfiguration, {
        props: {
          agentId: 'test-agent',
          onSave: () => {}
        }
      });
      expect(container.querySelector('.rag-configuration')).toBeTruthy();
      expect(container.querySelector('.config-header')).toBeTruthy();
      expect(container.querySelector('.config-sections')).toBeTruthy();
    });
  });

  describe('GraphFlowBuilder', () => {
    it('should render without errors', () => {
      const { container } = render(GraphFlowBuilder, {
        props: {
          workflowId: 'test-workflow',
          onSave: () => {}
        }
      });
      expect(container.querySelector('.graphflow-builder')).toBeTruthy();
      expect(container.querySelector('.builder-header')).toBeTruthy();
      expect(container.querySelector('.canvas-container')).toBeTruthy();
    });
  });

  describe('HITLApprovalInterface', () => {
    it('should render without errors', () => {
      const { container } = render(HITLApprovalInterface, {
        props: {
          userId: 'test-user',
          onApproval: () => {}
        }
      });
      expect(container.querySelector('.hitl-interface')).toBeTruthy();
      expect(container.querySelector('.interface-header')).toBeTruthy();
      expect(container.querySelector('.approvals-list')).toBeTruthy();
    });
  });
});