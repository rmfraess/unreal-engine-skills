#pragma once

#include "CoreMinimal.h"
#include "GameFramework/SaveGame.h"
#include "UObject/Object.h"
#include "SkillAuditTypes.generated.h"

USTRUCT()
struct FSkillAuditPayload
{
    GENERATED_BODY()

    UPROPERTY()
    TObjectPtr<UObject> Target;
};

UCLASS()
class USkillAuditOwner : public UObject
{
    GENERATED_BODY()

public:
    UPROPERTY()
    FSkillAuditPayload Payload;

    // DELEGATE-01: a native handle must not be a reflected property.
    FDelegateHandle ListenerHandle;

    UFUNCTION(BlueprintCallable, CallInEditor, Category="Audit")
    void SpecifierButton() {}

    UFUNCTION(BlueprintCallable, Category="Audit", meta=(CallInEditor="true"))
    void MetadataButton() {}
};

UCLASS()
class USkillAuditSave : public ULocalPlayerSaveGame
{
    GENERATED_BODY()

public:
    UPROPERTY()
    int32 OrdinaryValue = 0;

    UPROPERTY(SaveGame)
    int32 MarkedValue = 0;

    UPROPERTY(Transient)
    int32 TransientValue = 0;

    bool bSawSaveGameArchive = false;
    bool bHandledPostLoad = false;

    void Serialize(FArchive& Ar) override
    {
        bSawSaveGameArchive = Ar.IsSaveGame();
        Super::Serialize(Ar);
    }

    void HandlePostLoad() override
    {
        bHandledPostLoad = true;
        Super::HandlePostLoad();
    }
};
