using UnrealBuildTool;

public class SkillAuditP1 : ModuleRules
{
    public SkillAuditP1(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PrivateDependencyModuleNames.AddRange(new string[]
        {
            "Core", "CoreUObject", "Engine", "AudioMixer", "FunctionalTesting", "EnhancedInput",
            "Niagara", "Projects", "Json"
        });
    }
}
