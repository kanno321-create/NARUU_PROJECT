/**
 * useEstimate Hook
 * Manages estimate calculation and validation
 */

import { useState, useCallback } from 'react';
import {
  createEstimate,
  validateEstimate as validateEstimateApi,
  rerunEstimate,
} from '../api/estimates';
import type {
  EstimateRequest,
  EstimateResponse,
  ValidateEstimateRequest,
  ValidateEstimateResponse,
} from '../types/estimate';

interface UseEstimateReturn {
  calculateEstimate: (request: EstimateRequest) => Promise<EstimateResponse>;
  validateEstimate: (
    request: ValidateEstimateRequest
  ) => Promise<ValidateEstimateResponse>;
  recalculateEstimate: (estimateId: string) => Promise<EstimateResponse>;
  isCalculating: boolean;
  isValidating: boolean;
  result: EstimateResponse | null;
  validationResult: ValidateEstimateResponse | null;
  error: string | null;
  clearError: () => void;
  clearResults: () => void;
}

export function useEstimate(): UseEstimateReturn {
  const [isCalculating, setIsCalculating] = useState(false);
  const [isValidating, setIsValidating] = useState(false);
  const [result, setResult] = useState<EstimateResponse | null>(null);
  const [validationResult, setValidationResult] =
    useState<ValidateEstimateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const calculateEstimate = useCallback(
    async (request: EstimateRequest): Promise<EstimateResponse> => {
      setIsCalculating(true);
      setError(null);

      try {
        const response = await createEstimate(request);
        setResult(response);
        return response;
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : '견적 계산 중 오류가 발생했습니다';
        setError(errorMessage);
        throw err;
      } finally {
        setIsCalculating(false);
      }
    },
    []
  );

  const validateEstimate = useCallback(
    async (
      request: ValidateEstimateRequest
    ): Promise<ValidateEstimateResponse> => {
      setIsValidating(true);
      setError(null);

      try {
        const response = await validateEstimateApi(request);
        setValidationResult(response);
        return response;
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : '검증 중 오류가 발생했습니다';
        setError(errorMessage);
        throw err;
      } finally {
        setIsValidating(false);
      }
    },
    []
  );

  const recalculateEstimate = useCallback(
    async (estimateId: string): Promise<EstimateResponse> => {
      setIsCalculating(true);
      setError(null);

      try {
        const response = await rerunEstimate(estimateId);
        setResult(response);
        return response;
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : '재계산 중 오류가 발생했습니다';
        setError(errorMessage);
        throw err;
      } finally {
        setIsCalculating(false);
      }
    },
    []
  );

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const clearResults = useCallback(() => {
    setResult(null);
    setValidationResult(null);
    setError(null);
  }, []);

  return {
    calculateEstimate,
    validateEstimate,
    recalculateEstimate,
    isCalculating,
    isValidating,
    result,
    validationResult,
    error,
    clearError,
    clearResults,
  };
}
