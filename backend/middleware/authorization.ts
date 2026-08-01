/**
 * ============================================================================
 * Smart Care Agent - Authorization Middleware
 * 多租戶權限隔離架構 - 後端授權中介軟體
 * ============================================================================
 * 版本: 2.0
 * 日期: 2026-08-01
 * 語言: TypeScript / Node.js
 * ============================================================================
 */

import { Request, Response, NextFunction } from 'express';
import { PrismaClient, AccountType, OrganizationRole } from '@prisma/client';

const prisma = new PrismaClient();

// ============================================================================
// 授權上下文介面
// ============================================================================

export interface AuthContext {
  userId: string;
  accountType: AccountType;
  organizationIds: string[];
  authorizedPersonaIds: string[];
  permissions: PersonaPermissions;
  organizationRole?: OrganizationRole;
}

export interface PersonaPermissions {
  [personaId: string]: {
    canReadProfile: boolean;
    canReadHealth: boolean;
    canReadMedication: boolean;
    canReadConversation: boolean;
    canCreateEvent: boolean;
    canUpdateEvent: boolean;
    canManageReminder: boolean;
    canAcknowledgeAlert: boolean;
    canApproveAiAction: boolean;
  };
}

// ============================================================================
// 錯誤類別
// ============================================================================

export class UnauthorizedError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'UnauthorizedError';
  }
}

export class ForbiddenError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ForbiddenError';
  }
}

// ============================================================================
// 1. Session 驗證中介軟體
// ============================================================================

/**
 * 驗證 Session Token 並載入使用者資訊
 */
export async function authenticateSession(
  req: Request,
  res: Response,
  next: NextFunction
) {
  try {
    // 取得 Authorization Header
    const authHeader = req.headers.authorization;
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      throw new UnauthorizedError('Missing or invalid authorization header');
    }

    const token = authHeader.substring(7); // 移除 "Bearer "
    
    // 計算 Token Hash（實際應使用 SHA-256）
    const crypto = require('crypto');
    const tokenHash = crypto.createHash('sha256').update(token).digest('hex');

    // 查詢 Session
    const session = await prisma.authSession.findUnique({
      where: { sessionTokenHash: tokenHash },
      include: { user: true },
    });

    // 驗證 Session
    if (!session) {
      throw new UnauthorizedError('Invalid session token');
    }

    if (session.expiresAt < new Date()) {
      throw new UnauthorizedError('Session expired');
    }

    if (session.revokedAt) {
      throw new UnauthorizedError('Session revoked');
    }

    if (!session.user.isActive) {
      throw new UnauthorizedError('User account is inactive');
    }

    // 更新最後活動時間
    await prisma.authSession.update({
      where: { sessionTokenHash: tokenHash },
      data: { lastSeenAt: new Date() },
    });

    // 儲存使用者資訊到 Request
    req.user = session.user;

    next();
  } catch (error) {
    if (error instanceof UnauthorizedError) {
      return res.status(401).json({ error: error.message });
    }
    console.error('Authentication error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}

// ============================================================================
// 2. 組織範圍驗證中介軟體
// ============================================================================

/**
 * 驗證使用者對目標組織的存取權限
 */
export async function authorizeOrganization(
  req: Request,
  res: Response,
  next: NextFunction
) {
  try {
    const user = req.user;
    if (!user) {
      throw new UnauthorizedError('User not authenticated');
    }

    const targetOrganizationId = req.body.organizationId || req.params.organizationId;
    
    if (!targetOrganizationId) {
      throw new ForbiddenError('Organization ID is required');
    }

    // 根據帳號類型驗證
    switch (user.accountType) {
      case 'SYSTEM_ADMIN':
        // 系統管理員：記錄稽核後允許（應使用獨立管理 API）
        await auditLog({
          requestId: req.id,
          actorType: 'USER',
          actorId: user.userId,
          actionType: 'ADMIN_ACCESS',
          resourceType: 'organization',
          resourceId: targetOrganizationId,
          result: 'ALLOWED',
          reason: 'System admin access',
        });
        break;

      case 'ORGANIZATION_MEMBER':
        // 機構人員：檢查成員資格
        const membership = await prisma.organizationMember.findFirst({
          where: {
            userId: user.userId,
            organizationId: targetOrganizationId,
            status: 'active',
            OR: [
              { startsAt: null },
              { startsAt: { lte: new Date() } },
            ],
            AND: [
              {
                OR: [
                  { endsAt: null },
                  { endsAt: { gt: new Date() } },
                ],
              },
            ],
          },
        });

        if (!membership) {
          throw new ForbiddenError('No active membership in this organization');
        }

        req.organizationRole = membership.organizationRole;
        break;

      case 'ELDER':
      case 'FAMILY_GUARDIAN':
        // 長者與家屬：透過 Persona 關聯檢查組織
        // 後續在 authorizePersona 中處理
        break;

      default:
        throw new ForbiddenError('Invalid account type');
    }

    req.authorizedOrganizationId = targetOrganizationId;
    next();
  } catch (error) {
    if (error instanceof ForbiddenError) {
      return res.status(403).json({ error: error.message });
    }
    console.error('Organization authorization error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}

// ============================================================================
// 3. 長者範圍驗證中介軟體
// ============================================================================

/**
 * 驗證使用者對目標長者的存取權限
 */
export async function authorizePersona(
  req: Request,
  res: Response,
  next: NextFunction
) {
  try {
    const user = req.user;
    if (!user) {
      throw new UnauthorizedError('User not authenticated');
    }

    const targetPersonaId = req.body.personaId || req.params.personaId;
    const targetOrganizationId = req.authorizedOrganizationId;

    if (!targetPersonaId) {
      throw new ForbiddenError('Persona ID is required');
    }

    // 根據帳號類型驗證
    switch (user.accountType) {
      case 'ELDER':
        // 長者只能存取自己的資料
        // 假設長者帳號與 Persona 1:1 對應（需根據實際設計調整）
        const elderPersona = await prisma.persona.findFirst({
          where: {
            personaId: targetPersonaId,
            // 實際應透過 AppUser.personaId 或其他關聯檢查
          },
        });

        if (!elderPersona || elderPersona.personaId !== targetPersonaId) {
          throw new ForbiddenError('Can only access own data');
        }

        req.permissions = getElderPermissions(targetPersonaId);
        break;

      case 'FAMILY_GUARDIAN':
        // 家屬：檢查監護關係
        const guardianship = await prisma.guardianRelationship.findFirst({
          where: {
            userId: user.userId,
            personaId: targetPersonaId,
            revokedAt: null,
            OR: [
              { startsAt: null },
              { startsAt: { lte: new Date() } },
            ],
            AND: [
              {
                OR: [
                  { expiresAt: null },
                  { expiresAt: { gt: new Date() } },
                ],
              },
            ],
          },
        });

        if (!guardianship) {
          throw new ForbiddenError('No active guardianship for this persona');
        }

        req.permissions = getGuardianPermissions(guardianship);
        break;

      case 'ORGANIZATION_MEMBER':
        // 機構人員：檢查長者是否在該機構
        const organizationPersona = await prisma.organizationPersona.findFirst({
          where: {
            organizationId: targetOrganizationId,
            personaId: targetPersonaId,
            status: 'active',
          },
        });

        if (!organizationPersona) {
          throw new ForbiddenError('Persona not found in this organization');
        }

        // 檢查細粒度權限
        const userAccess = await prisma.userPersonaAccess.findFirst({
          where: {
            userId: user.userId,
            personaId: targetPersonaId,
            organizationId: targetOrganizationId,
            revokedAt: null,
            OR: [
              { startsAt: null },
              { startsAt: { lte: new Date() } },
            ],
            AND: [
              {
                OR: [
                  { expiresAt: null },
                  { expiresAt: { gt: new Date() } },
                ],
              },
            ],
          },
        });

        if (!userAccess) {
          throw new ForbiddenError('No access permission for this persona');
        }

        req.permissions = getOrganizationMemberPermissions(
          userAccess,
          req.organizationRole
        );
        break;

      case 'SYSTEM_ADMIN':
        // 系統管理員：完整權限但記錄稽核
        await auditLog({
          requestId: req.id,
          actorType: 'USER',
          actorId: user.userId,
          organizationId: targetOrganizationId,
          personaId: targetPersonaId,
          actionType: 'ADMIN_ACCESS',
          resourceType: 'persona',
          resourceId: targetPersonaId,
          result: 'ALLOWED',
          reason: 'System admin access',
        });
        req.permissions = getAdminPermissions(targetPersonaId);
        break;

      default:
        throw new ForbiddenError('Invalid account type');
    }

    req.authorizedPersonaId = targetPersonaId;
    next();
  } catch (error) {
    if (error instanceof ForbiddenError || error instanceof UnauthorizedError) {
      return res.status(error instanceof ForbiddenError ? 403 : 401).json({
        error: error.message,
      });
    }
    console.error('Persona authorization error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}

// ============================================================================
// 4. 操作權限檢查
// ============================================================================

/**
 * 檢查特定操作權限
 */
export function requirePermission(permission: keyof PersonaPermissions[string]) {
  return (req: Request, res: Response, next: NextFunction) => {
    const permissions = req.permissions;
    const personaId = req.authorizedPersonaId;

    if (!permissions || !permissions[personaId]) {
      return res.status(403).json({ error: 'No permissions found' });
    }

    if (!permissions[personaId][permission]) {
      return res.status(403).json({
        error: `Permission denied: ${permission}`,
      });
    }

    next();
  };
}

// ============================================================================
// 5. AI 操作驗證
// ============================================================================

/**
 * 驗證 AI Agent 的操作權限
 */
export async function authorizeAiOperation(
  servicePrincipalId: string,
  operation: string,
  resourceType: string,
  organizationId: string,
  personaId: string
): Promise<boolean> {
  // 檢查服務主體是否存在且啟用
  const servicePrincipal = await prisma.servicePrincipal.findUnique({
    where: { servicePrincipalId },
    include: { permissions: true },
  });

  if (!servicePrincipal || servicePrincipal.status !== 'active') {
    return false;
  }

  // 檢查是否有對應權限
  const hasPermission = servicePrincipal.permissions.some(
    (p) => p.resourceType === resourceType && p.action === operation
  );

  if (!hasPermission) {
    return false;
  }

  // 記錄稽核
  await auditLog({
    requestId: `ai_${Date.now()}`,
    actorType: 'AI',
    servicePrincipalId,
    organizationId,
    personaId,
    actionType: operation,
    resourceType,
    result: 'ALLOWED',
    reason: 'AI operation authorized',
  });

  return true;
}

/**
 * AI 建立工具執行的驗證
 */
export async function authorizeAiToolExecution(
  servicePrincipalId: string,
  toolName: string,
  organizationId: string,
  personaId: string,
  riskLevel: string
): Promise<{ allowed: boolean; requiresConfirmation: boolean }> {
  // 檢查 AI 是否有執行該工具的權限
  const hasPermission = await authorizeAiOperation(
    servicePrincipalId,
    'tool_execution.propose',
    'tool_execution',
    organizationId,
    personaId
  );

  if (!hasPermission) {
    return { allowed: false, requiresConfirmation: false };
  }

  // 根據風險等級決定是否需要確認
  const requiresConfirmation = ['HIGH', 'CRITICAL'].includes(riskLevel);

  return { allowed: true, requiresConfirmation };
}

// ============================================================================
// 6. 權限輔助函數
// ============================================================================

/**
 * 取得長者的權限（只能存取自己的資料）
 */
function getElderPermissions(personaId: string): PersonaPermissions {
  return {
    [personaId]: {
      canReadProfile: true,
      canReadHealth: true,
      canReadMedication: true,
      canReadConversation: true,
      canCreateEvent: false,
      canUpdateEvent: false,
      canManageReminder: false,
      canAcknowledgeAlert: false,
      canApproveAiAction: false,
    },
  };
}

/**
 * 取得家屬的權限（基於監護關係）
 */
function getGuardianPermissions(
  guardianship: any
): PersonaPermissions {
  return {
    [guardianship.personaId]: {
      canReadProfile: guardianship.canReadProfile,
      canReadHealth: guardianship.canReadHealthData,
      canReadMedication: guardianship.canReadMedication,
      canReadConversation: guardianship.canReadConversation,
      canCreateEvent: guardianship.canCreateCareEvent,
      canUpdateEvent: guardianship.canUpdateCarePlan,
      canManageReminder: false,
      canAcknowledgeAlert: false,
      canApproveAiAction: guardianship.canApproveAiAction,
    },
  };
}

/**
 * 取得機構人員的權限（基於角色與細粒度權限）
 */
function getOrganizationMemberPermissions(
  userAccess: any,
  role?: OrganizationRole
): PersonaPermissions {
  // 基礎權限來自 UserPersonaAccess
  const basePermissions = {
    canReadProfile: userAccess.canReadProfile,
    canReadHealth: userAccess.canReadHealth,
    canReadMedication: userAccess.canReadMedication,
    canReadConversation: userAccess.canReadConversation,
    canCreateEvent: userAccess.canCreateEvent,
    canUpdateEvent: userAccess.canUpdateEvent,
    canManageReminder: userAccess.canManageReminder,
    canAcknowledgeAlert: userAccess.canAcknowledgeAlert,
    canApproveAiAction: userAccess.canApproveAiAction,
  };

  // 根據組織角色提升權限
  if (role === 'ORG_ADMIN' || role === 'CARE_MANAGER') {
    basePermissions.canApproveAiAction = true;
    basePermissions.canAcknowledgeAlert = true;
  }

  if (role === 'NURSE') {
    basePermissions.canReadHealth = true;
    basePermissions.canReadMedication = true;
    basePermissions.canCreateEvent = true;
  }

  return {
    [userAccess.personaId]: basePermissions,
  };
}

/**
 * 取得系統管理員的權限（完整權限）
 */
function getAdminPermissions(personaId: string): PersonaPermissions {
  return {
    [personaId]: {
      canReadProfile: true,
      canReadHealth: true,
      canReadMedication: true,
      canReadConversation: true,
      canCreateEvent: true,
      canUpdateEvent: true,
      canManageReminder: true,
      canAcknowledgeAlert: true,
      canApproveAiAction: true,
    },
  };
}

// ============================================================================
// 7. 稽核日誌
// ============================================================================

/**
 * 寫入稽核日誌
 */
async function auditLog(data: {
  requestId: string;
  actorType: 'USER' | 'AI' | 'SYSTEM' | 'SERVICE';
  actorId?: string;
  servicePrincipalId?: string;
  organizationId?: string;
  personaId?: string;
  actionType: string;
  resourceType: string;
  resourceId?: string;
  result: string;
  reason?: string;
  metadata?: any;
}) {
  try {
    await prisma.auditLog.create({
      data: {
        ...data,
        createdAt: new Date(),
      },
    });
  } catch (error) {
    console.error('Failed to write audit log:', error);
    // 稽核失敗不應阻塞業務操作，但應記錄錯誤
  }
}

// ============================================================================
// 8. 使用範例
// ============================================================================

/*
// Express.js 路由範例

import express from 'express';
const router = express.Router();

// 查詢長者資料
router.get('/personas/:personaId', 
  authenticateSession,           // 1. 驗證登入
  authorizeOrganization,          // 2. 驗證組織權限
  authorizePersona,               // 3. 驗證長者權限
  requirePermission('canReadProfile'), // 4. 檢查讀取權限
  async (req, res) => {
    const personaId = req.params.personaId;
    
    const persona = await prisma.persona.findUnique({
      where: { personaId },
      select: {
        personaId: true,
        displayName: true,
        preferredLanguage: true,
        // 不返回 primary_organization_id
      },
    });
    
    res.json(persona);
  }
);

// 建立照護事件
router.post('/care-events',
  authenticateSession,
  authorizeOrganization,
  authorizePersona,
  requirePermission('canCreateEvent'),
  async (req, res) => {
    const { personaId, eventType, content } = req.body;
    
    const careEvent = await prisma.careEvent.create({
      data: {
        organizationId: req.authorizedOrganizationId,
        personaId,
        eventType,
        content,
        createdByType: 'USER',
        createdById: req.user.userId,
        memoryStatus: 'CANDIDATE',
      },
    });
    
    // 寫入稽核日誌
    await auditLog({
      requestId: req.id,
      actorType: 'USER',
      actorId: req.user.userId,
      organizationId: req.authorizedOrganizationId,
      personaId,
      actionType: 'CREATE',
      resourceType: 'care_event',
      resourceId: careEvent.eventId,
      result: 'SUCCESS',
    });
    
    res.json(careEvent);
  }
);

// AI 建立工具執行
router.post('/ai/tool-executions',
  authenticateSession, // AI 服務也需要認證
  async (req, res) => {
    const { servicePrincipalId, toolName, organizationId, personaId, riskLevel } = req.body;
    
    // 驗證 AI 權限
    const { allowed, requiresConfirmation } = await authorizeAiToolExecution(
      servicePrincipalId,
      toolName,
      organizationId,
      personaId,
      riskLevel
    );
    
    if (!allowed) {
      return res.status(403).json({ error: 'AI operation not authorized' });
    }
    
    // 建立工具執行記錄
    const toolExecution = await prisma.toolExecution.create({
      data: {
        organizationId,
        personaId,
        servicePrincipalId,
        toolName,
        toolStatus: 'PROPOSED',
        riskLevel,
        // ...其他欄位
      },
    });
    
    // 如果需要確認，建立確認請求
    if (requiresConfirmation) {
      await prisma.confirmationRequest.create({
        data: {
          organizationId,
          personaId,
          requestedByServiceId: servicePrincipalId,
          targetType: 'tool_execution',
          targetId: toolExecution.toolExecutionId,
          confirmationQuestion: `Confirm AI tool execution: ${toolName}`,
          confirmationStatus: 'PENDING',
        },
      });
    }
    
    res.json({ 
      toolExecution, 
      requiresConfirmation 
    });
  }
);

export default router;
*/

// ============================================================================
// 完成
// ============================================================================

export {
  authenticateSession,
  authorizeOrganization,
  authorizePersona,
  requirePermission,
  authorizeAiOperation,
  authorizeAiToolExecution,
  auditLog,
};
