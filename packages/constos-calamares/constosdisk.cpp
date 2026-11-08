// SPDX-License-Identifier: GPL-3.0-or-later
#include "GlobalStorage.h"
#include "JobQueue.h"
#include "utils/PluginFactory.h"
#include "viewpages/ViewStep.h"

#include <QComboBox>
#include <QFile>
#include <QFont>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QLabel>
#include <QLineEdit>
#include <QStringList>
#include <QVBoxLayout>

class DiskStep : public Calamares::ViewStep
{
    Q_OBJECT

public:
    explicit DiskStep(QObject* parent = nullptr)
        : Calamares::ViewStep(parent)
    {
    }

    QString prettyName() const override { return tr("Disk"); }
    bool isNextEnabled() const override { return !selectedPath().isEmpty() && m_confirmation->text() == selectedPath(); }
    bool isBackEnabled() const override { return true; }
    bool isAtBeginning() const override { return true; }
    bool isAtEnd() const override { return true; }
    Calamares::JobList jobs() const override { return {}; }

    QString prettyStatus() const override
    {
        if (!isNextEnabled())
            return {};
        return tr("<strong>Use the entire disk %1</strong><br/>%2<br/>"
                  "Create an EFI system partition (1 GiB) and a Btrfs system partition.")
            .arg(m_disks->currentText().toHtmlEscaped(), m_details->text().toHtmlEscaped());
    }

    QWidget* widget() override
    {
        if (m_page)
            return m_page;

        m_page = new QWidget;
        auto* content = new QWidget;
        content->setMaximumWidth(680);
        auto* pageLayout = new QVBoxLayout(m_page);
        pageLayout->setContentsMargins(16, 16, 16, 16);
        pageLayout->addWidget(content);
        pageLayout->addStretch();
        auto* layout = new QVBoxLayout(content);
        layout->setContentsMargins(0, 0, 0, 0);
        layout->setSpacing(12);

        auto* title = label(tr("Choose an empty disk"));
        auto font = title->font();
        font.setBold(true);
        font.setPointSizeF(font.pointSizeF() * 1.3);
        title->setFont(font);
        layout->addWidget(title);
        layout->addWidget(label(tr("ConstOS uses the entire disk. Only fixed, empty disks of at least 32 GiB are shown.")));

        m_disks = new QComboBox;
        m_disks->setSizeAdjustPolicy(QComboBox::AdjustToMinimumContentsLengthWithIcon);
        m_disks->setMinimumContentsLength(24);
        auto* diskLabel = label(tr("&Target disk"));
        diskLabel->setBuddy(m_disks);
        layout->addWidget(diskLabel);
        layout->addWidget(m_disks);
        m_details = label({});
        layout->addWidget(m_details);

        layout->addSpacing(8);
        layout->addWidget(label(tr("Planned layout: EFI system partition (1 GiB) and Btrfs with system, home, and snapshot subvolumes.")));
        m_pathLabel = label(tr("Confirm the disk &path"));
        m_confirmation = new QLineEdit;
        m_pathLabel->setBuddy(m_confirmation);
        layout->addWidget(m_pathLabel);
        layout->addWidget(m_confirmation);
        m_hint = label({});
        layout->addWidget(m_hint);

        QFile input(QStringLiteral("/run/constos-installer/eligible-disks.json"));
        if (input.open(QIODevice::ReadOnly))
        {
            const auto disks = QJsonDocument::fromJson(input.readAll()).array();
            for (const auto& candidate : disks)
            {
                const auto disk = candidate.toObject();
                const auto path = disk.value("path").toString();
                const auto size = disk.value("size").toDouble() / (1024.0 * 1024 * 1024);
                m_disks->addItem(tr("%1 · %2 GiB").arg(path, QString::number(size, 'f', 1)), disk);
            }
        }
        m_disks->setPlaceholderText(tr("Select a disk"));
        m_disks->setCurrentIndex(-1);
        connect(m_disks, &QComboBox::currentIndexChanged, this, [this] {
            m_confirmation->clear();
            updateSelection();
        });
        connect(m_confirmation, &QLineEdit::textChanged, this, &DiskStep::updateSelection);
        updateSelection();
        return m_page;
    }

private:
    static QLabel* label(const QString& text)
    {
        auto* result = new QLabel(text);
        result->setTextFormat(Qt::PlainText);
        result->setWordWrap(true);
        return result;
    }

    QJsonObject selectedDisk() const
    {
        return m_disks ? m_disks->currentData().value<QJsonObject>() : QJsonObject {};
    }

    QString selectedPath() const { return selectedDisk().value("path").toString(); }

    void updateSelection()
    {
        const auto disk = selectedDisk();
        const auto path = disk.value("path").toString();
        const auto model = disk.value("model").toString().simplified();
        const auto serial = disk.value("serial").toString().simplified();
        const auto wwn = disk.value("wwn").toString().simplified();
        const auto deviceId = disk.value("maj:min").toString();
        QStringList details;
        if (!path.isEmpty())
        {
            if (!model.isEmpty())
                details << tr("Model: %1").arg(model);
            if (!serial.isEmpty())
                details << tr("Serial: %1").arg(serial);
            if (!wwn.isEmpty())
                details << tr("WWN: %1").arg(wwn);
            details << tr("Device ID: %1").arg(deviceId);
        }
        m_details->setText(details.join(QStringLiteral("  ·  ")));
        m_details->setVisible(!path.isEmpty());
        m_pathLabel->setText(path.isEmpty() ? tr("Confirm the disk &path") : tr("&Type %1 to confirm the target").arg(path));
        m_confirmation->setEnabled(!path.isEmpty());
        m_confirmation->setPlaceholderText(path);
        const bool ready = isNextEnabled();
        if (!m_disks->count())
            m_hint->setText(tr("No eligible empty disk found. Close and reopen the installer after connecting one."));
        else if (!m_confirmation->text().isEmpty() && !ready)
            m_hint->setText(tr("The path does not match the selected disk."));
        else
            m_hint->setText(tr("Nothing is written until you choose Install on the Summary page."));

        auto* state = Calamares::JobQueue::instance()->globalStorage();
        state->insert(QStringLiteral("constosDiskPath"), path);
        state->insert(QStringLiteral("constosDiskConfirmation"), ready ? m_confirmation->text() : QString());
        Q_EMIT nextStatusChanged(ready);
    }

    QWidget* m_page = nullptr;
    QComboBox* m_disks = nullptr;
    QLabel* m_details = nullptr;
    QLabel* m_pathLabel = nullptr;
    QLineEdit* m_confirmation = nullptr;
    QLabel* m_hint = nullptr;
};

CALAMARES_PLUGIN_FACTORY_DECLARATION(DiskStepFactory)
CALAMARES_PLUGIN_FACTORY_DEFINITION(DiskStepFactory, registerPlugin<DiskStep>();)

#include "constosdisk.moc"
