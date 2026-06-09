using UnityEngine;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Collections.Concurrent;

public class NickUDPReceiver : MonoBehaviour
{
    public int port = 39540; // Изменили порт, чтобы избежать конфликтов
    private UdpClient udpClient;
    private ConcurrentQueue<string> commandQueue = new ConcurrentQueue<string>();
    
    private AvatarAnimatorReceiver animatorReceiver;
    private UniversalBlendshapes currentBlendshapes;

    void Start()
    {
        animatorReceiver = FindFirstObjectByType<AvatarAnimatorReceiver>();
        StartServer();
    }

    void StartServer()
    {
        try
        {
            udpClient = new UdpClient(port);
            udpClient.BeginReceive(ReceiveCallback, null);
            Debug.Log($"<color=#00FF00>[Nick]</color> UDP Сервер успешно запущен на порту {port}");
        }
        catch (System.Exception e)
        {
            Debug.LogError($"<color=#FF0000>[Nick]</color> Ошибка запуска UDP: {e.Message}");
        }
    }

    private void ReceiveCallback(System.IAsyncResult ar)
    {
        try
        {
            IPEndPoint endpoint = new IPEndPoint(IPAddress.Any, port);
            byte[] data = udpClient.EndReceive(ar, ref endpoint);
            string message = Encoding.UTF8.GetString(data);
            
            commandQueue.Enqueue(message);
            udpClient.BeginReceive(ReceiveCallback, null);
        }
        catch (System.ObjectDisposedException) { /* Игнорируем при закрытии */ }
        catch (System.Exception e) { Debug.LogError($"[Nick] Ошибка UDP: {e.Message}"); }
    }

    void Update()
    {
        // Обрабатываем очередь команд в главном потоке Unity
        while (commandQueue.TryDequeue(out string command))
        {
            ProcessCommand(command);
        }
    }

    private void ProcessCommand(string command)
    {
        Debug.Log($"<color=#00FFFF>[Nick]</color> Команда: {command}");
        
        // Ищем активный аватар, если он поменялся
        if (animatorReceiver == null || animatorReceiver.avatarAnimator == null)
        {
            animatorReceiver = FindFirstObjectByType<AvatarAnimatorReceiver>();
            if (animatorReceiver == null) return;
        }

        // Ищем скрипт лица на текущем аватаре
        if (currentBlendshapes == null)
        {
            currentBlendshapes = animatorReceiver.avatarAnimator.GetComponent<UniversalBlendshapes>();
            if (currentBlendshapes == null) 
            {
                currentBlendshapes = animatorReceiver.avatarAnimator.GetComponentInChildren<UniversalBlendshapes>(true);
            }
        }

        if (command.StartsWith("EMOTION:"))
        {
            string emotion = command.Split(':')[1];
            SetEmotion(emotion);
        }
        else if (command.StartsWith("ANIM:"))
        {
            string animType = command.Split(':')[1];
            if (animType == "Talk")
            {
                Animator anim = animatorReceiver.avatarAnimator;
                if (anim != null) anim.SetBool("isIdle", false);
            }
        }
    }

    private void SetEmotion(string emotionName)
    {
        if (currentBlendshapes == null) 
        {
            Debug.LogWarning("[Nick] Лицо (UniversalBlendshapes) не найдено на аватаре!");
            return;
        }

        // 1. Сбрасываем старые эмоции
        currentBlendshapes.Joy = 0f;
        currentBlendshapes.Angry = 0f;
        currentBlendshapes.Sorrow = 0f;
        currentBlendshapes.Fun = 0f;
        currentBlendshapes.Neutral = 0f;

        // 2. Включаем новую (на 100%)
        switch (emotionName)
        {
            case "Joy": currentBlendshapes.Joy = 1f; break;
            case "Angry": currentBlendshapes.Angry = 1f; break;
            case "Sorrow": currentBlendshapes.Sorrow = 1f; break;
            case "Fun": currentBlendshapes.Fun = 1f; break;
            case "Neutral": currentBlendshapes.Neutral = 1f; break;
            default: currentBlendshapes.Neutral = 1f; break;
        }
    }

    void OnApplicationQuit()
    {
        if (udpClient != null) udpClient.Close();
    }
}