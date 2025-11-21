from laser import Laser
from oscilloscope import Oscilloscope
from powermeter import PowerMeter
import sys

def test_laser():
    print("\n🔍 Тест лазера (моторов)...")
    laser = Laser()
    if laser.connect(com_port=30):
        print("✅ Лазер подключён")
        pos = laser.get_position(motor_id=1)
        print(f"Текущая позиция мотора 1: {pos} шагов")
        laser.disconnect()
    else:
        print("❌ Не удалось подключиться к лазеру")

def test_oscilloscope():
    print("\n🔍 Тест осциллографа...")
    scope = Oscilloscope()
    if scope.connect():
        print("✅ Осциллограф подключён")
        x, y = scope.get_current_data()
        if x is not None and y is not None:
            print(f"✅ Получены данные: {len(x)} точек")
        else:
            print("⚠️ Данные не получены")
        scope.disconnect()
    else:
        print("❌ Осциллограф не найден")

def test_powermeter():
    print("\n🔍 Тест измерителя энергии...")
    pm = PowerMeter()
    if pm.connect(com_port=5):
        print("✅ Измеритель энергии подключён")
        pm.set_wavelength(532)
        energy = pm.get_energy(n=3)
        unit = pm.get_unit()
        print(f"Энергия: {energy:.3e} {unit}")
        pm.zero_calibrate()
        pm.disconnect()
    else:
        print("❌ Не удалось подключиться к измерителю энергии")

def main():
    print("🧪 Тест подключения оборудования (без монохроматора)")
    print("=" * 60)

    try:
        test_oscilloscope()
        test_powermeter()
        test_laser()
    except KeyboardInterrupt:
        print("\n⚠️ Прервано пользователем")
    except Exception as exception:
        print(f"\n❌ Критическая ошибка: {exception}")
        sys.exit(1)

    print("\n✅ Тест завершён")

if __name__ == "__main__":
    main()
