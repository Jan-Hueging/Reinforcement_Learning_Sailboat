// file: SailLimitPlugin.cc
#include <gz/sim/System.hh>
#include <gz/sim/Model.hh>
#include <gz/sim/Joint.hh>
#include <gz/sim/World.hh>
#include <gz/sim/Util.hh>
#include <gz/plugin/Register.hh>
#include <gz/transport/Node.hh>
#include <gz/msgs/double.pb.h>
#include <gz/sim/components/JointPositionLimitsCmd.hh>
#include <gz/math/Vector2.hh>

#include <mutex>
#include <cmath>

using namespace gz;
using namespace gz::sim;

class SailLimitPlugin
  : public System,
    public ISystemConfigure,
    public ISystemPreUpdate
{
public:
  void Configure(const Entity &entity,
                 const std::shared_ptr<const sdf::Element> &sdf,
                 EntityComponentManager &ecm,
                 EventManager &) override
  {
    this->model = Model(entity);

    if (!this->model.Valid(ecm))
    {
      gzerr << "[SailLimitPlugin] Model invalid.\n";
      return;
    }

    if (sdf->HasElement("joint_name"))
      this->jointName = sdf->Get<std::string>("joint_name");
    else
      this->jointName = "sail_joint";

    if (sdf->HasElement("max_rate"))
      this->maxRate = sdf->Get<double>("max_rate");
    else
      this->maxRate = 0.2; // rad/s (~11.5 Grad/s)

    // DYNAMISCHE PFAD-AUFLÖSUNG: Holt den exakten Topic-Namen ohne Geister-Präfixe
    if (sdf->HasElement("topic"))
      this->topicName = sdf->Get<std::string>("topic");
    else
      this->topicName = "/Segelstellung_Soll";

    this->jointEntity = this->model.JointByName(ecm, this->jointName);
    if (this->jointEntity == kNullEntity)
    {
      gzerr << "[SailLimitPlugin] Joint '" << this->jointName << "' nicht gefunden.\n";
      return;
    }

    // Gazebo Transport-Knoten abonnieren
    this->node.Subscribe(this->topicName, &SailLimitPlugin::OnCmd, this);

    gzmsg << "[SailLimitPlugin] Hoert erfolgreich auf Topic: " << this->topicName
          << " fuer Gelenk: '" << this->jointName << "'\n";
  }

    void PreUpdate(const UpdateInfo &info,
                 EntityComponentManager &ecm) override
  {
    if (info.paused || this->jointEntity == kNullEntity)
      return;

    const double dt = std::chrono::duration<double>(info.dt).count();

    double targetLimitLocal;
    {
      std::lock_guard<std::mutex> lock(this->mutex);
      targetLimitLocal = this->targetLimit; 
    }

    // RAMPE: Sanftes Fieren/Dichtnehmen
    double diff = targetLimitLocal - this->currentLimit;
    const double maxStep = this->maxRate * dt;

    if (std::abs(diff) > maxStep)
      this->currentLimit += (diff > 0 ? 1.0 : -1.0) * maxStep;
    else
      this->currentLimit = targetLimitLocal;

    double lowerBound = -std::abs(this->currentLimit);
    double upperBound =  std::abs(this->currentLimit);

    using namespace gz::sim::components;
    using gz::math::Vector2d;

    auto limits = ecm.Component<JointPositionLimitsCmd>(this->jointEntity);

    // NEU: HIER PRÜFEN WIR, OB EINE AKTUALISIERUNG ÜBERHAUPT NÖTIG IST
    bool updateRequired = false;

    if (!limits)
    {
      updateRequired = true;
    }
    else
    {
      const auto &currentData = limits->Data();
      if (currentData.empty())
      {
        updateRequired = true;
      }
      else
      {
        // Wenn die Abweichung zum aktuell in Gazebo gesetzten Limit größer als 1e-4 rad ist,
        // erst dann greifen wir modifizierend in die Physik ein.
        if (std::abs(currentData[0].X() - lowerBound) > 1e-4 || 
            std::abs(currentData[0].Y() - upperBound) > 1e-4)
        {
          updateRequired = true;
        }
      }
    }

    // Nur in die Gazebo-Struktur schreiben, wenn sich die Schot bewegt hat!
    if (updateRequired)
    {
      if (!limits)
      {
        std::vector<Vector2d> data(1);
        data[0].Set(lowerBound, upperBound);
        ecm.CreateComponent(this->jointEntity, JointPositionLimitsCmd(data));
      }
      else
      {
        auto &data = limits->Data();
        if (data.size() < 1)
          data.resize(1);

        data[0].Set(lowerBound, upperBound);
        
        // Signalisiert Gazebo, dass sich die Komponente geändert hat
        ecm.SetChanged(this->jointEntity, JointPositionLimitsCmd::typeId, ComponentState::OneTimeChange);
      }
    }
  }


private:
  void OnCmd(const gz::msgs::Double &msg)
  {
    std::lock_guard<std::mutex> lock(this->mutex);

    double cmd = msg.data();
    double mag = std::abs(cmd);
    
    // Begrenzung auf das physikalische Maximum (90 Grad)
    this->targetLimit = std::min(mag, this->maxPhysLimit);
  }

private:
  Model model{kNullEntity};
  Entity jointEntity{kNullEntity};

  std::string jointName{"sail_joint"};
  std::string topicName{"/Segelstellung_Soll"};

  transport::Node node;

  // HIER GEBEN WIR DEM SEGEL DIE GEWÜNSCHTE GRUNDÖFFNUNG BEIM START (0.1 rad ≈ 6°)
  double currentLimit{0.0};   
  double targetLimit{0.5};    

  double maxRate{0.2};        
  double maxPhysLimit{1.57};  

  std::mutex mutex;
};

GZ_ADD_PLUGIN(SailLimitPlugin, System, ISystemConfigure, ISystemPreUpdate)
GZ_ADD_PLUGIN_ALIAS(SailLimitPlugin, "gz::sim::systems::SailLimitPlugin")
