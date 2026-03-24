import {
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Box,
  Typography,
  useTheme,
} from "@mui/material";
import {
  ExpandMore as ExpandMoreIcon,
  SmartToy as BotIcon,
  Psychology as ThinkIcon,
} from "@mui/icons-material";
import React from "react";

interface ThinkBlockProps {
  steps: string[];
  currentStep?: string;
  isThinking: boolean;
}

export const ThinkBlock: React.FC<ThinkBlockProps> = ({
  steps,
  currentStep,
  isThinking,
}) => {
  const theme = useTheme();

  const allSteps = currentStep ? [...steps, currentStep] : steps;

  if (allSteps.length === 0 && !isThinking) return null;

  return (
    <Box
      sx={{
        display: "flex",
        gap: 1.5,
        mb: 2,
        flexDirection: "row",
        alignItems: "flex-start",
      }}
    >
      <Box
        sx={{
          width: 32,
          height: 32,
          borderRadius: "50%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          bgcolor: theme.palette.grey[600],
          color: "#fff",
          flexShrink: 0,
        }}
      >
        <BotIcon sx={{ fontSize: 18 }} />
      </Box>
      <Accordion
        defaultExpanded={isThinking}
        sx={{
          maxWidth: "70%",
          bgcolor:
            theme.palette.mode === "dark"
              ? theme.palette.grey[900]
              : theme.palette.grey[50],
          border: `1px solid ${theme.palette.divider}`,
          borderRadius: "8px !important",
          boxShadow: "none",
          "&::before": { display: "none" },
          "& .MuiAccordionSummary-root": {
            minHeight: 36,
            px: 1.5,
          },
          "& .MuiAccordionSummary-content": {
            my: 0.5,
          },
        }}
      >
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <ThinkIcon
              sx={{
                fontSize: 18,
                color: theme.palette.text.secondary,
                animation: isThinking ? "spin 2s linear infinite" : "none",
                "@keyframes spin": {
                  "0%": { transform: "rotate(0deg)" },
                  "100%": { transform: "rotate(360deg)" },
                },
              }}
            />
            <Typography variant="body2" color="text.secondary" fontWeight={500}>
              Think
              {isThinking && "ing..."}
            </Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails sx={{ pt: 0, px: 1.5, pb: 1 }}>
          {allSteps.map((step, i) => {
            const isLast = i === allSteps.length - 1;
            const isCurrent = isLast && isThinking;
            return (
              <Box
                key={i}
                sx={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: 1,
                  py: 0.3,
                }}
              >
                <Typography
                  variant="caption"
                  sx={{
                    color: theme.palette.text.disabled,
                    userSelect: "none",
                    lineHeight: 1.8,
                  }}
                >
                  {isCurrent ? "›" : "✓"}
                </Typography>
                <Typography
                  variant="body2"
                  sx={{
                    color: isCurrent
                      ? theme.palette.text.primary
                      : theme.palette.text.secondary,
                    opacity: isCurrent ? 1 : 0.7,
                  }}
                >
                  {step}
                  {isCurrent && (
                    <Box
                      component="span"
                      sx={{
                        display: "inline-block",
                        width: 5,
                        height: 12,
                        bgcolor: "currentColor",
                        ml: 0.5,
                        animation: "blink 1s step-end infinite",
                        "@keyframes blink": {
                          "0%, 100%": { opacity: 1 },
                          "50%": { opacity: 0 },
                        },
                      }}
                    />
                  )}
                </Typography>
              </Box>
            );
          })}
        </AccordionDetails>
      </Accordion>
    </Box>
  );
};
