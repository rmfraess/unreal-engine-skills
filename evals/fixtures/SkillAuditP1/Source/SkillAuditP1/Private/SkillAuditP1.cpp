#include "SkillAuditTypes.h"

#include "AudioMixerBlueprintLibrary.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Dom/JsonObject.h"
#include "FunctionalTest.h"
#include "InputActionValue.h"
#include "Kismet/GameplayStatics.h"
#include "Math/Quat.h"
#include "Misc/AutomationTest.h"
#include "Misc/CommandLine.h"
#include "Modules/ModuleManager.h"
#include "NiagaraDataChannelAccessContext.h"
#include "NiagaraDataChannelFunctionLibrary.h"
#include "PluginReferenceDescriptor.h"
#include "ProjectDescriptor.h"
#include "Stats/Stats.h"
#include "Templates/SharedPointer.h"
#include "TimerManager.h"
#include "UObject/Class.h"
#include "UObject/StrongObjectPtr.h"
#include "UObject/UObjectGlobals.h"
#include <type_traits>

IMPLEMENT_PRIMARY_GAME_MODULE(FDefaultGameModuleImpl, SkillAuditP1, "SkillAuditP1");

// Compile-time API checks; not audio playback or functional-test cleanup coverage.
static_assert(std::is_same_v<decltype(&UAudioMixerBlueprintLibrary::AddSubmixEffect),
    int32 (*)(const UObject*, USoundSubmix*, USoundEffectSubmixPreset*)>);
static_assert(std::is_same_v<decltype(&AFunctionalTest::RegisterAutoDestroyActor),
    void (AFunctionalTest::*)(AActor*)>);
static_assert(std::is_same_v<TSharedPtr<int32>, TSharedPtr<int32, ESPMode::ThreadSafe>>);
static_assert(std::is_same_v<decltype(&UNiagaraDataChannelLibrary::WriteToNiagaraDataChannel_WithContext),
    UNiagaraDataChannelWriter* (*)(const UObject*, const UNiagaraDataChannelAsset*,
        FNDCAccessContextInst&, int32, bool, bool, bool, const FString&)>);

DECLARE_STATS_GROUP(TEXT("Skill Audit"), STATGROUP_SkillAudit, STATCAT_Advanced);
DECLARE_CYCLE_STAT_EXTERN(TEXT("Contract Probe"), STAT_SkillAuditProbe, STATGROUP_SkillAudit, SKILLAUDITP1_API);
DEFINE_STAT(STAT_SkillAuditProbe);

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSkillAuditP1Test, "SkillAudit.P1.CoreContracts",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FSkillAuditP1Test::RunTest(const FString& Parameters)
{
    SCOPE_CYCLE_COUNTER(STAT_SkillAuditProbe);

    // Stock slot serialization uses these memory helpers. No slot or production save is written.
    TStrongObjectPtr<USkillAuditSave> Save(NewObject<USkillAuditSave>());
    Save->OrdinaryValue = 7;
    Save->MarkedValue = 11;
    Save->TransientValue = 13;
    TArray<uint8> SaveBytes;
    if (TestTrue(TEXT("Save memory serialization succeeds"),
        UGameplayStatics::SaveGameToMemory(Save.Get(), SaveBytes)))
    {
        TStrongObjectPtr<USkillAuditSave> Loaded(
            Cast<USkillAuditSave>(UGameplayStatics::LoadGameFromMemory(SaveBytes)));
        if (TestNotNull(TEXT("Generic memory load constructs concrete save"), Loaded.Get()))
        {
            TestEqual(TEXT("Ordinary property survives without SaveGame specifier"), Loaded->OrdinaryValue, 7);
            TestEqual(TEXT("SaveGame-marked property survives"), Loaded->MarkedValue, 11);
            TestEqual(TEXT("Transient property is excluded"), Loaded->TransientValue, 0);
            TestFalse(TEXT("Stock memory loader does not set ArIsSaveGame"), Loaded->bSawSaveGameArchive);
            TestFalse(TEXT("Generic load does not call local-player HandlePostLoad"), Loaded->bHandledPostLoad);
        }
    }
    TestNull(TEXT("Empty save data is rejected"), UGameplayStatics::LoadGameFromMemory(TArray<uint8>()));

    FTimerManager TimerManager(nullptr);
    FTimerHandle NextTickHandle = TimerManager.SetTimerForNextTick(TFunction<void()>([]() {}));
    TestTrue(TEXT("Next-tick timer returns a live handle"),
        NextTickHandle.IsValid() && TimerManager.TimerExists(NextTickHandle));
    const FTimerHandle OriginalHandle = NextTickHandle;
    TimerManager.ClearTimer(NextTickHandle);
    TestFalse(TEXT("ClearTimer invalidates next-tick handle"), NextTickHandle.IsValid());
    TestFalse(TEXT("Cleared next-tick timer is absent"), TimerManager.TimerExists(OriginalHandle));

    FNDCAccessContextInst AccessContext;
    if (TestTrue(TEXT("Niagara access context initializes"),
        AccessContext.Init(TNDCAccessContextType(FNDCAccessContext::StaticStruct()))))
    {
        FNDCAccessContext& Context = AccessContext.GetChecked<FNDCAccessContext>();
        Context.Location = FVector(1.0, 2.0, 3.0);
        Context.bOverrideLocation = true;
        TestTrue(TEXT("Niagara access context retains routing location"),
            AccessContext.GetChecked<FNDCAccessContext>().Location.Equals(FVector(1.0, 2.0, 3.0)));
    }

    // In-memory descriptors only: no project files, plugin discovery, or activation changes.
    TSharedRef<FJsonObject> PluginJson = MakeShared<FJsonObject>();
    PluginJson->SetStringField(TEXT("Name"), TEXT("SkillAuditExample"));
    PluginJson->SetBoolField(TEXT("Enabled"), true);
    PluginJson->SetBoolField(TEXT("Activate"), true);
    PluginJson->SetNumberField(TEXT("Version"), 5);
    FPluginReferenceDescriptor PluginDescriptor;
    FText FailReason;
    TestTrue(TEXT("Plugin reference parses"), PluginDescriptor.Read(PluginJson, &FailReason));
    TestTrue(TEXT("Serialized Version sets RequestedVersion"),
        PluginDescriptor.RequestedVersion.IsSet() && PluginDescriptor.RequestedVersion.GetValue() == 5);
    TestTrue(TEXT("Serialized Activate sets activation flag"), PluginDescriptor.bActivate);
    PluginJson->SetBoolField(TEXT("Enabled"), false);
    FPluginReferenceDescriptor DisabledPlugin;
    TestFalse(TEXT("Version pin on disabled plugin is rejected"), DisabledPlugin.Read(PluginJson, &FailReason));

    FJsonObject ProjectJson;
    ProjectJson.SetNumberField(TEXT("FileVersion"), 3);
    ProjectJson.SetBoolField(TEXT("Enterprise"), true);
    ProjectJson.SetBoolField(TEXT("DisableEnginePluginsByDefault"), true);
    FProjectDescriptor ProjectDescriptor;
    TestTrue(TEXT("Project reference parses"), ProjectDescriptor.Read(ProjectJson, FString(), FailReason));
    TestTrue(TEXT("Serialized project keys set both flags"),
        ProjectDescriptor.bIsEnterpriseProject && ProjectDescriptor.bDisableEnginePluginsByDefault);

    TestEqual(TEXT("Default string assertion ignores case"),
        FString(TEXT("Example")), FString(TEXT("example")));

    const FInputActionValue Axis(FVector2D(0.0, 1.0));
    TestTrue(TEXT("Axis2D converted to bool is not silently false"), Axis.Get<bool>());
    const FInputActionValue Button(true);
    TestTrue(TEXT("Boolean converted to Axis2D preserves X"),
        Button.Get<FVector2D>().Equals(FVector2D(1.0, 0.0)));
    TestTrue(TEXT("Getter conversion leaves declared type unchanged"),
        Button.GetValueType() == EInputActionValueType::Boolean);

    // Transient, unregistered components: CPU contracts only, not rendering evidence.
    TStrongObjectPtr<UStaticMeshComponent> Mesh(NewObject<UStaticMeshComponent>());
    const FTransform MeshTransform(FRotator(0.0, 30.0, 0.0), FVector(100.0, 200.0, 300.0));
    Mesh->SetWorldTransform(MeshTransform);
    const FName MissingSocket(TEXT("SkillAuditMissingSocket"));
    TestFalse(TEXT("Missing socket is reported absent"), Mesh->DoesSocketExist(MissingSocket));
    TestTrue(TEXT("Missing socket returns component world transform"),
        Mesh->GetSocketTransform(MissingSocket, RTS_World).Equals(MeshTransform));
    TestTrue(TEXT("Missing socket in component space is identity"),
        Mesh->GetSocketTransform(MissingSocket, RTS_Component).Equals(FTransform::Identity));

    TStrongObjectPtr<UInstancedStaticMeshComponent> Instances(NewObject<UInstancedStaticMeshComponent>());
    Instances->SetNumCustomDataFloats(2);
    const int32 InstanceIndex = Instances->AddInstance(FTransform::Identity);
    TestTrue(TEXT("Custom data write succeeds"), Instances->SetCustomDataValue(InstanceIndex, 0, 7.0f));
    Instances->SetNumCustomDataFloats(2);
    TestTrue(TEXT("Same count preserves existing custom data"),
        Instances->PerInstanceSMCustomData.Num() == 2 && Instances->PerInstanceSMCustomData[0] == 7.0f);
    Instances->SetNumCustomDataFloats(4);
    TestEqual(TEXT("Changed count resizes existing instance data"), Instances->PerInstanceSMCustomData.Num(), 4);
    for (const float Value : Instances->PerInstanceSMCustomData)
    {
        TestEqual(TEXT("Changed count resets custom data"), Value, 0.0f);
    }

    // Both forms are consumed as CallInEditor metadata by PropertyCustomizationHelpers.
    for (const FName FunctionName : { FName(TEXT("SpecifierButton")), FName(TEXT("MetadataButton")) })
    {
        const UFunction* Function = USkillAuditOwner::StaticClass()->FindFunctionByName(FunctionName);
        if (TestNotNull(TEXT("Reflected editor button exists"), Function))
        {
            TestTrue(*FunctionName.ToString(), Function->GetBoolMetaData(TEXT("CallInEditor")));
            TestEqual(TEXT("Editor button requires no parameters"), Function->ParmsSize, uint16(0));
        }
    }

    const FQuat A(FVector::UpVector, UE_PI / 2.0);
    const FQuat B(FVector::RightVector, UE_PI / 2.0);
    const FVector Input = FVector::ForwardVector;
    const FVector Actual = (A * B).RotateVector(Input);
    TestTrue(TEXT("Quaternion product applies right operand first"),
        Actual.Equals(A.RotateVector(B.RotateVector(Input)), 1.e-6));
    TestFalse(TEXT("Noncommuting rotations reject the old reversed order"),
        Actual.Equals(B.RotateVector(A.RotateVector(Input)), 1.e-6));

    TStrongObjectPtr<USkillAuditOwner> Owner(NewObject<USkillAuditOwner>());
    Owner->Payload.Target = NewObject<USkillAuditOwner>(Owner.Get());
    const TWeakObjectPtr<UObject> Target = Owner->Payload.Target.Get();
    const TWeakObjectPtr<UObject> OwnerKey = Owner.Get();
    TMap<TWeakObjectPtr<UObject>, int32, FDefaultSetAllocator,
        TWeakObjectPtrMapKeyFuncs<TWeakObjectPtr<UObject>, int32>> WeakKeyMap;
    WeakKeyMap.Add(OwnerKey, 1);
    WeakKeyMap.Add(Target, 2);
    CollectGarbage(RF_NoFlags, true);
    TestTrue(TEXT("Reflected nested struct retains its UObject reference"), Target.IsValid());
    Owner->Payload.Target = nullptr;
    CollectGarbage(RF_NoFlags, true);
    TestFalse(TEXT("Outer alone does not retain the child after clearing its property"),
        Target.IsValid());
    Owner.Reset();
    CollectGarbage(RF_NoFlags, true);
    TestFalse(TEXT("Weak map key does not keep owner alive"), OwnerKey.IsValid());
    TestTrue(TEXT("Ordinary equality collapses different stale weak pointers"), OwnerKey == Target);
    TestFalse(TEXT("Identity comparison distinguishes stale objects"),
        OwnerKey.HasSameIndexAndSerialNumber(Target));
    TestEqual(TEXT("Explicit engine weak key funcs preserve first stale key"), WeakKeyMap.FindRef(OwnerKey), 1);
    TestEqual(TEXT("Explicit engine weak key funcs preserve second stale key"), WeakKeyMap.FindRef(Target), 2);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSkillAuditAutomationFailureProbe,
    "SkillAudit.P2.AutomationFailureProbe",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FSkillAuditAutomationFailureProbe::RunTest(const FString& Parameters)
{
    if (FParse::Param(FCommandLine::Get(), TEXT("SkillAuditIntentionalFailure")))
    {
        AddError(TEXT("Intentional failure selected by -SkillAuditIntentionalFailure."));
    }
    return true;
}
