import sys
import importlib.metadata

def generate_requirements():
    print("📋 Создаю requirements.txt...")
    
    installed_packages = importlib.metadata.distributions()
    
    requirements = []
    for dist in installed_packages:
        name = dist.metadata['Name']
        version = dist.version
        
        if name.lower() in ['pip', 'setuptools', 'wheel']:
            continue
        requirements.append(f"{name}=={version}")
    
    requirements.sort()
    
    with open("requirements.txt", "w", encoding="utf-8") as f:
        f.write("--index-url https://download.pytorch.org/whl/cu124\n")
        for req in requirements:
            f.write(req + "\n")
            
    print("✅ Файл requirements.txt успешно создан!")

if __name__ == "__main__":
    generate_requirements()