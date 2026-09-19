using UnrealBuildTool;

public class SkillAuditP1EditorTarget : TargetRules
{
    public SkillAuditP1EditorTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Editor;
        DefaultBuildSettings = BuildSettingsVersion.V7;
        IncludeOrderVersion = EngineIncludeOrderVersion.Unreal5_8;
        ExtraModuleNames.Add("SkillAuditP1");
    }
}
