using UnityEngine;
using VRM; 

public class NickLipSync : MonoBehaviour
{
    [Header("Настройки Громкости")]
    public float sensitivity = 10f; 
    public float smoothSpeed = 20f;

    [Header("Пороги частот (У -> А -> И)")]
    [Tooltip("Ниже этого значения — чистый звук У")]
    public float zcrU = 15f; 
    [Tooltip("В этом диапазоне — чистый звук А")]
    public float zcrA = 45f; 
    [Tooltip("Выше этого значения — чистый звук И")]
    public float zcrI = 80f;

    private string micName;
    private AudioClip micClip;
    private UniversalBlendshapes blendshapes;
    private VRMBlendShapeProxy vrmProxy; 
    
    // Плавные значения для каждой мышцы
    private float currentA = 0f;
    private float currentI = 0f;
    private float currentU = 0f;
    
    private int lastPos = 0;
    private int stuckFrames = 0;

    void Start()
    {
        foreach (var device in Microphone.devices)
        {
            if (device.Contains("CABLE Output") || device.Contains("Virtual Cable"))
            {
                micName = device;
                if (device.Contains("Output")) break;
            }
        }

        if (string.IsNullOrEmpty(micName) && Microphone.devices.Length > 0)
            micName = Microphone.devices[0];

        if (!string.IsNullOrEmpty(micName))
        {
            micClip = Microphone.Start(micName, true, 1, 48000);
        }
    }

    void LateUpdate()
    {
        if (blendshapes == null && vrmProxy == null)
        {
            var receiver = FindFirstObjectByType<AvatarAnimatorReceiver>();
            if (receiver != null && receiver.avatarAnimator != null)
            {
                blendshapes = receiver.avatarAnimator.GetComponentInChildren<UniversalBlendshapes>(true);
                vrmProxy = receiver.avatarAnimator.GetComponentInChildren<VRMBlendShapeProxy>(true);
            }
            return;
        }

        if (micClip == null) return;

        int currentPosition = Microphone.GetPosition(micName);

        // Защита от зависания буфера Windows
        if (currentPosition == lastPos) 
        {
            stuckFrames++;
            if (stuckFrames > 60) return; 
        } 
        else stuckFrames = 0;
        lastPos = currentPosition;

        int sampleSize = 1024; 
        if (currentPosition < sampleSize) return;

        float[] data = new float[sampleSize];
        micClip.GetData(data, currentPosition - sampleSize);

        float sum = 0f;
        int zeroCrossings = 0;

        for (int i = 0; i < sampleSize; i++)
        {
            sum += data[i] * data[i]; 
            
            if (i > 0)
            {
                if ((data[i] > 0 && data[i - 1] < 0) || (data[i] < 0 && data[i - 1] > 0))
                {
                    zeroCrossings++;
                }
            }
        }
        
        // 1. Считаем общую громкость
        float rms = Mathf.Sqrt(sum / sampleSize);
        float totalOpen = Mathf.Clamp01(rms * sensitivity);

        // 2. Распределяем веса между У, А и И на основе частоты (Zero Crossings)
        float weightU = 0f;
        float weightA = 0f;
        float weightI = 0f;

        if (zeroCrossings <= zcrA)
        {
            // Плавный переход от У к А
            weightA = Mathf.InverseLerp(zcrU, zcrA, zeroCrossings);
            weightU = 1f - weightA;
        }
        else
        {
            // Плавный переход от А к И
            weightI = Mathf.InverseLerp(zcrA, zcrI, zeroCrossings);
            weightA = 1f - weightI;
        }

        // 3. Высчитываем итоговое открытие для каждой мышцы
        float targetU = totalOpen * weightU;
        float targetA = totalOpen * weightA;
        float targetI = totalOpen * weightI;

        currentU = Mathf.Lerp(currentU, targetU, Time.deltaTime * smoothSpeed);
        currentA = Mathf.Lerp(currentA, targetA, Time.deltaTime * smoothSpeed);
        currentI = Mathf.Lerp(currentI, targetI, Time.deltaTime * smoothSpeed);

        // --- ПРИМЕНЯЕМ К АВАТАРУ ---
        
        if (blendshapes != null)
        {
            blendshapes.A = currentA;
            blendshapes.I = currentI;
            blendshapes.U = currentU;
        }

        if (vrmProxy != null)
        {
            vrmProxy.ImmediatelySetValue(BlendShapeKey.CreateFromPreset(BlendShapePreset.A), currentA);
            vrmProxy.ImmediatelySetValue(BlendShapeKey.CreateFromPreset(BlendShapePreset.I), currentI);
            vrmProxy.ImmediatelySetValue(BlendShapeKey.CreateFromPreset(BlendShapePreset.U), currentU);
        }
    }
}