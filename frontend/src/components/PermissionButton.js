import React from 'react';
import { Button, Tooltip } from 'antd';
import { usePermissions } from '../context/PermissionContext';

const PermissionButton = ({ 
  children, 
  permission, 
  permissions, 
  requireAll = true,
  customsCode,
  adminOnly = false,
  tooltip = "您没有权限执行此操作",
  disabled = false,
  ...buttonProps 
}) => {
  const { 
    hasPermission, 
    hasAnyPermission, 
    hasAllPermissions, 
    hasCustomsCodeAccess, 
    isAdmin 
  } = usePermissions();

  let hasAccess = true;
  let disabledReason = '';

  // 检查管理员权限
  if (adminOnly && !isAdmin()) {
    hasAccess = false;
    disabledReason = '需要管理员权限';
  }

  // 检查单个权限
  if (hasAccess && permission && !hasPermission(permission)) {
    hasAccess = false;
    disabledReason = '权限不足';
  }

  // 检查多个权限
  if (hasAccess && permissions && permissions.length > 0) {
    const hasRequiredPermissions = requireAll 
      ? hasAllPermissions(permissions)
      : hasAnyPermission(permissions);
    
    if (!hasRequiredPermissions) {
      hasAccess = false;
      disabledReason = '权限不足';
    }
  }

  // 检查海关编码权限
  if (hasAccess && customsCode && !hasCustomsCodeAccess(customsCode)) {
    hasAccess = false;
    disabledReason = '无权限访问该海关编码';
  }

  const isDisabled = disabled || !hasAccess;
  const tooltipTitle = !hasAccess ? (disabledReason || tooltip) : '';

  if (!hasAccess && buttonProps.style?.display !== 'none') {
    // 如果没有权限且不是隐藏按钮，显示禁用状态
    return (
      <Tooltip title={tooltipTitle}>
        <Button {...buttonProps} disabled={true}>
          {children}
        </Button>
      </Tooltip>
    );
  }

  if (!hasAccess) {
    // 如果没有权限且需要隐藏，返回null
    return null;
  }

  return (
    <Button {...buttonProps} disabled={isDisabled}>
      {children}
    </Button>
  );
};

export default PermissionButton;